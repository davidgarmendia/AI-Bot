import asyncio
import os
import time
import requests
from playsound import playsound
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        # Definimos la ruta base del proyecto
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.audio_dir = os.path.join(self.base_dir, "temp_audios")
        self.queue = asyncio.Queue()
        
        # --- CONFIGURACIÓN DE ALLTALK ---
        self.alltalk_url = "http://127.0.0.1:7851/api/tts-generate"
        self.voice_name = "female_03.wav" 
        # --------------------------------
        
        self._limpiar_audios()

    def _limpiar_audios(self):
        """Crea la carpeta de audios temporales si no existe."""
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    async def agregar_a_cola(self, texto):
        """Añade texto a la fila de espera para ser hablado."""
        if texto and len(texto.strip()) > 0:
            await self.queue.put(texto)

    async def worker(self):
        """Procesa la cola de mensajes y los envía a AllTalk."""
        print(f"🔊 AllTalk Engine activo. Voz actual: {self.voice_name}")
        while True:
            # Esperamos a que llegue un nuevo mensaje
            texto = await self.queue.get()
            
            # Nombre base único (sin extensión para la API)
            temp_name_simple = f"kim_voice_{int(time.time())}"
            # Ruta completa con extensión para que playsound la encuentre
            full_path = os.path.join(self.audio_dir, f"{temp_name_simple}.wav")
            
            try:
                # El Diccionario (Data Payload)
                # IMPORTANTE: output_file_name va sin '.wav' porque AllTalk lo agrega solo
                data = {
                    "text_input": str(texto),
                    "voice_speaker": self.voice_name,
                    "language": "es",
                    "output_file_name": temp_name_simple,
                    "use_cache": "true",
                    "speed": "1.0"
                }

                # Realizamos la petición POST a AllTalk
                response = await asyncio.to_thread(
                    requests.post, 
                    self.alltalk_url, 
                    data=data, 
                    timeout=25
                )

                if response.status_code == 200:
                    print(f"🎙️ Kim dice: {texto}")
                    # Reproducimos el audio generado
                    # Nota: AllTalk guarda por defecto en su propia carpeta 'outputs'
                    # pero si configuraste AllTalk para usar tu carpeta temp, lo encontrará aquí:
                    await asyncio.to_thread(playsound, full_path)
                else:
                    print(f"❌ Error API AllTalk: {response.status_code} - {response.text}")

                # Intentamos limpiar el archivo generado para no acumular basura
                if os.path.exists(full_path):
                    os.remove(full_path)
                    
            except Exception as e:
                print(f"❌ Error en el proceso de TTS: {e}")
            
            finally:
                # Marcamos la tarea como terminada en la cola
                self.queue.task_done()