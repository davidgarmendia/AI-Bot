import asyncio
import os
import time
import requests
import pygame
import re
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        self.queue = asyncio.Queue()
        
        self.alltalk_url = self.loader.get_env("ALLTALK_URL")
        self.voice_name = self.loader.get_env("ALLTALK_VOICE")
        self.alltalk_outputs_path = self.loader.get_env("ALLTALK_OUTPUT_PATH")

        # Verificación mínima de arranque
        if not self.alltalk_outputs_path or not os.path.exists(self.alltalk_outputs_path):
            print(f"❌ Error: Ruta de audio no encontrada.")
        
        try:
            pygame.mixer.quit()
            pygame.mixer.pre_init(44100, -16, 2, 2048) 
            pygame.mixer.init()
            pygame.mixer.music.set_volume(1.0)
            print(f"🔊 Kim Vocal Engine: Online ({self.voice_name})")
        except Exception as e:
            print(f"⚠️ Error Mixer: {e}")

    def _corregir_genero(self, texto):
        reemplazos = {
            r"\bidentificado\b": "identificada", r"\bbienvenido\b": "bienvenida",
            r"\blisto\b": "lista", r"\bcansado\b": "cansada",
            r"\bconectado\b": "conectada", r"\bvivo\b": "viva",
            r"\bamigo\b": "amiga", r"\bsolo\b": "sola"
        }
        for patron, reemplazo in reemplazos.items():
            texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
        return texto

    async def reproducir_y_esperar(self, texto):
        if not texto or not texto.strip():
            return

        texto = self._corregir_genero(texto)
        temp_name = f"kim_{int(time.time())}"
        base_path = Path(self.alltalk_outputs_path)
        full_path = base_path / f"{temp_name}.wav"
        
        try:
            data = {
                "text_input": str(texto), "voice_speaker": self.voice_name,
                "language": "es", "output_file_name": temp_name,
                "use_cache": "false", "speed": "1.0"
            }

            response = await asyncio.to_thread(
                requests.post, self.alltalk_url, data=data, timeout=25
            )

            if response.status_code == 200:
                archivo_final = None
                
                # Búsqueda silenciosa (máximo 4 seg)
                for _ in range(12):
                    await asyncio.sleep(0.3)
                    if full_path.exists():
                        archivo_final = full_path
                        break
                    
                    # Backup: Sabueso silencioso
                    wavs = list(base_path.glob("*.wav"))
                    if wavs:
                        reciente = max(wavs, key=os.path.getmtime)
                        if time.time() - os.path.getmtime(reciente) < 5:
                            archivo_final = reciente
                            break
                
                if archivo_final:
                    print(f"🎙️ Kim: {texto[:50]}...")
                    pygame.mixer.music.load(str(archivo_final.absolute()))
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    
                    pygame.mixer.music.unload()
                    try: os.remove(str(archivo_final))
                    except: pass
                    return True
            else:
                print(f"❌ Error AllTalk API: {response.status_code}")
        except Exception as e:
            print(f"❌ Error TTS: {e}")
        
        return False

    async def worker(self):
        while True:
            texto = await self.queue.get()
            await self.reproducir_y_esperar(texto)
            self.queue.task_done()