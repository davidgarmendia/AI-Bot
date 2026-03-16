import asyncio
import os
import time
import requests
import pygame  # Cambiamos a pygame porque es más estable para hilos
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        # Mantenemos la cola para otros usos, pero añadiremos un método directo
        self.queue = asyncio.Queue()
        
        self.alltalk_url = self.loader.get_env("ALLTALK_URL")
        self.voice_name = self.loader.get_env("ALLTALK_VOICE")
        self.alltalk_outputs_path = self.loader.get_env("ALLTALK_OUTPUT_PATH")

        # Inicializamos el mezclador de audio una sola vez
        pygame.mixer.init()

    async def reproducir_y_esperar(self, texto):
        """
        Este método es la clave: genera el audio, lo reproduce 
        y NO termina hasta que el audio deja de sonar.
        """
        if not texto or len(texto.strip()) == 0:
            return

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

            # 1. Pedimos el audio a AllTalk
            response = await asyncio.to_thread(
                requests.post, self.alltalk_url, data=data, timeout=25
            )

            if response.status_code == 200:
                # 2. Pequeña espera de seguridad para que el sistema de archivos suelte el .wav
                await asyncio.sleep(0.5) 
                
                if os.path.exists(full_path):
                    print(f"🎙️ Reproduciendo: {texto[:30]}...")
                    
                    # 3. Reproducción controlada con Pygame
                    pygame.mixer.music.load(full_path)
                    pygame.mixer.music.play()
                    
                    # 4. Bucle de espera: Mientras el audio suene, nos quedamos aquí
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    
                    # Limpieza obligatoria tras sonar
                    pygame.mixer.music.unload() 
                    os.remove(full_path)
                    return True
            else:
                print(f"❌ Error API AllTalk: {response.status_code}")
        except Exception as e:
            print(f"❌ Error en TTS Sincronizado: {e}")
        
        return False

    async def worker(self):
        """Mantenemos el worker por si envías cosas a la cola de forma genérica"""
        print(f"🔊 AllTalk Engine activo. Voz: {self.voice_name}")
        while True:
            texto = await self.queue.get()
            await self.reproducir_y_esperar(texto)
            self.queue.task_done()