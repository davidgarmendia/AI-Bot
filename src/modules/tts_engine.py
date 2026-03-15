import asyncio
import os
import time
import requests
from playsound import playsound
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        # Ruta base
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.audio_dir = os.path.join(self.base_dir, "temp_audios")
        self.queue = asyncio.Queue()
        
        # --- CONFIGURACIÓN DE ALLTALK ---
        self.alltalk_url = "http://127.0.0.1:7851/api/tts-generate"
        self.voice_name = "female_03.wav" 
        # --------------------------------
        
        self._limpiar_audios()

    def _limpiar_audios(self):
        """Crea la carpeta si no existe."""
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    async def agregar_a_cola(self, texto):
        """Añade texto a la cola."""
        if texto and len(texto.strip()) > 0:
            await self.queue.put(texto)

    async def worker(self):
        """ESTA ES LA FUNCIÓN QUE FALTABA O ESTABA MAL IDENTADA"""
        print(f"🔊 AllTalk Engine activo. Voz actual: {self.voice_name}")
        while True:
            texto = await self.queue.get()
            
            # Nombre sin extensión para la API
            temp_name_simple = f"kim_voice_{int(time.time())}"
            # Ruta con extensión para playsound
            full_path = os.path.join(self.audio_dir, f"{temp_name_simple}.wav")
            
            try:
                data = {
                    "text_input": str(texto),
                    "voice_speaker": self.voice_name,
                    "language": "es",
                    "output_file_name": temp_name_simple,
                    "use_cache": "true",
                    "speed": "1.0"
                }

                # Petición a AllTalk
                response = await asyncio.to_thread(
                    requests.post, 
                    self.alltalk_url, 
                    data=data, 
                    timeout=25
                )

                if response.status_code == 200:
                    # Pausa de seguridad para que Windows termine de escribir el archivo
                    await asyncio.sleep(0.6)
                    
                    if os.path.exists(full_path):
                        print(f"🎙️ Kim dice: {texto}")
                        await asyncio.to_thread(playsound, full_path)
                    else:
                        print(f"⚠️ Archivo no encontrado en: {full_path}")
                else:
                    print(f"❌ Error API AllTalk: {response.status_code}")

                # Limpieza de archivo
                if os.path.exists(full_path):
                    os.remove(full_path)
                    
            except Exception as e:
                print(f"❌ Error en TTS: {e}")
            
            finally:
                self.queue.task_done()