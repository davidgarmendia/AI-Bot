import json
import os
import time
from pathlib import Path

class MemoryManager:
    def __init__(self, memory_dir="memory", max_days=7):
        # Localizamos la raíz del proyecto (AI Bot)
        self.base_path = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
        self.memory_dir = self.base_path / memory_dir
        
        # Crear la carpeta de recuerdos si no existe
        if not self.memory_dir.exists():
            self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_seconds = max_days * 24 * 60 * 60
        self.max_messages = 15 

    def _get_user_file(self, user_id):
        # Limpiar el ID de usuario para que sea un nombre de archivo válido
        safe_id = "".join([c for c in str(user_id) if c.isalnum() or c in ("-", "_")])
        return self.memory_dir / f"{safe_id}.json"

    def get_context(self, user_id):
        user_file = self._get_user_file(user_id)
        if not user_file.exists():
            return []

        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            now = time.time()
            # Filtrar: Solo lo que tenga menos de 7 días
            history = [m for m in history if now - m.get('timestamp', 0) < self.max_seconds]
            return history[-self.max_messages:]
        except Exception as e:
            print(f"❌ Error memoria: {e}")
            return []

    def save_interaction(self, user_id, user_msg, bot_res):
        history = self.get_context(user_id)
        history.append({
            "timestamp": time.time(),
            "user": user_msg,
            "bot": bot_res
        })
        history = history[-self.max_messages:]

        try:
            with open(self._get_user_file(user_id), 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error al guardar JSON: {e}")