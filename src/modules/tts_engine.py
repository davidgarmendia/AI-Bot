import asyncio
import os
import time
import re
import shutil
import edge_tts
from playsound import playsound
from pathlib import Path

class TTSEngine:
    def __init__(self, loader):
        self.loader = loader
        # Ruta de audios temporales
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.audio_dir = os.path.join(self.base_dir, "temp_audios")
        
        # Cola de mensajes para evitar saturación
        self.queue = asyncio.Queue()
        
        # Diccionario fonético desde config.json
        self.phonetic_dict = self.loader.config.get("phonetic_replacements", {})
        
        # Limpiar carpeta de audios al iniciar
        self._limpiar_audios()

    def _limpiar_audios(self):
        """QA: Borra audios viejos para no llenar el disco."""
        if os.path.exists(self.audio_dir):
            shutil.rmtree(self.audio_dir)
        os.makedirs(self.audio_dir)

    def _aplicar_fonetica(self, texto):
        """Aplica los reemplazos de pronunciación (ej: Klumsy -> Clamsi)."""
        for original, fonetico in self.phonetic_dict.items():
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            texto = pattern.sub(fonetico, texto)
        return texto

    async def agregar_a_cola(self, texto):
        """Recibe texto del procesador y lo mete a la fila."""
        texto_fonetico = self._aplicar_fonetica(texto)
        await self.queue.put(texto_fonetico)

    async def worker(self):
        """El motor que siempre está escuchando la cola para hablar."""
        print("🔊 TTS Engine: Trabajador de voz activo.")
        while True:
            # Espera a que haya algo en la cola
            texto = await self.queue.get()
            
            filename = os.path.join(self.audio_dir, f"voice_{int(time.time())}.mp3")
            
            try:
                # 1. Generar el audio con Edge TTS (Voz de Dalia)
                communicate = edge_tts.Communicate(texto, "es-MX-DaliaNeural")
                await communicate.save(filename)
                
                # 2. Reproducir el audio (vía hilo para no bloquear el bot)
                await asyncio.to_thread(playsound, filename)
                
                # 3. Limpieza de archivo usado
                if os.path.exists(filename):
                    os.remove(filename)
                    
            except Exception as e:
                print(f"❌ Error en TTS Worker: {e}")
            
            self.queue.task_done()