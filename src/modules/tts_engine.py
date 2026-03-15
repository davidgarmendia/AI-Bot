import asyncio
import os
import time
import requests
from playsound import playsound
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.audio_dir = os.path.join(self.base_dir, "temp_audios")
        self.queue = asyncio.Queue()
        
        # --- CONFIGURACIÓN DE ALLTALK ---
        self.alltalk_url = "http://127.0.0.1:7851/api/tts-generate"
        self.voice_name = "female_03.wav" 
        # --------------------------------
        
        self._limpiar_audios()

    def _limpiar_audios(self):
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

    async def agregar_a_cola(self, texto):
        if texto and len(texto.strip()) > 0:
            await self.queue.put(texto)

    async def worker(self):
        print(f"🔊 AllTalk Engine activo. Voz actual: {self.voice_name}")
        while True:
            texto = await self.queue.get()
            
            # Solo el nombre del archivo, sin rutas raras de Windows
            temp_filename = f"kim_voice_{int(time.time())}.wav"
            full_path = os.path.join(self.audio_dir, temp_filename)
            
            try:
                # Diccionario (Data Payload) optimizado
                data = {
                    "text_input": str(texto),
                    "voice_speaker": self.voice_name,
                    "language": "es",
                    "output_file_name": temp_filename, # Solo el nombre
                    "use_cache": "true",
                    "speed": "1.0"
                }

                # Enviamos la petición
                response = await asyncio.to_thread(
                    requests.post, 
                    self.alltalk_url, 
                    data=data, 
                    timeout=20 # Evitamos que se quede colgado
                )

                if response.status_code == 200:
                    print(f"🎙️ Reproduciendo: {texto[:30]}...")
                    # Buscamos el archivo donde AllTalk suele guardarlos si no usa la ruta completa
                    # Si AllTalk no guarda en tu carpeta temp_audios, revisa su carpeta 'outputs'
                    await asyncio.to_thread(playsound, full_path)
                else:
                    print(f"❌ Error API AllTalk: {response.status_code} - {response.text}")

                if os.path.exists(full_path):
                    os.remove(full_path)
                    
            except Exception as e:
                print(f"❌ Error en TTS: {e}")
            
            finally:
                self.queue.task_done()