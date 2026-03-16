import asyncio
import os
import time
import requests
from playsound import playsound
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        self.queue = asyncio.Queue()
        
        # Cargamos directamente sin valores internos (Hardcoded)
        self.alltalk_url = self.loader.get_env("ALLTALK_URL")
        self.voice_name = self.loader.get_env("ALLTALK_VOICE")
        self.alltalk_outputs_path = self.loader.get_env("ALLTALK_OUTPUT_PATH")

    async def agregar_a_cola(self, texto):
        if texto and len(texto.strip()) > 0:
            await self.queue.put(texto)

    async def worker(self):
        # Verificación antes de arrancar
        if not self.alltalk_url or not self.alltalk_outputs_path:
            print("❌ TTS: Error de configuración. Revisa tu archivo .env")
            return

        print(f"🔊 AllTalk Engine activo. Voz: {self.voice_name}")
        
        while True:
            texto = await self.queue.get()
            temp_name = f"kim_voice_{int(time.time())}"
            full_path = os.path.join(self.alltalk_outputs_path, f"{temp_name}.wav")
            
            try:
                data = {
                    "text_input": str(texto),
                    "voice_speaker": self.voice_name,
                    "language": "es",
                    "output_file_name": temp_name,
                    "use_cache": "false",
                    "speed": "1.0"
                }

                response = await asyncio.to_thread(requests.post, self.alltalk_url, data=data, timeout=25)

                if response.status_code == 200:
                    await asyncio.sleep(0.7)
                    if os.path.exists(full_path):
                        print(f"🎙️ Kim dice: {texto}")
                        await asyncio.to_thread(playsound, full_path)
                        os.remove(full_path)
                else:
                    print(f"❌ Error API AllTalk: {response.status_code}")
            except Exception as e:
                print(f"❌ Error en TTS: {e}")
            finally:
                self.queue.task_done()