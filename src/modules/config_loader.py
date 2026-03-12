import json
import os
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self):
        # Localiza la raíz del proyecto (sube 2 niveles desde src/modules)
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        load_dotenv(os.path.join(self.base_dir, ".env"))

        # Rutas centralizadas
        self.paths = {
            "config": os.path.join(self.base_dir, "config", "config.json"),
            "dialogues": os.path.join(self.base_dir, "data", "dialogues.json"),
            "restricted": os.path.join(self.base_dir, "data", "restricted_terminology.json")
        }

        self.config = self._read_json(self.paths["config"], {})
        self.dialogues = self._read_json(self.paths["dialogues"], {"pools": {}})
        self.restricted_terms = self._read_json(self.paths["restricted"], {"blacklist": []}).get("blacklist", [])
        
        print("✅ ConfigLoader: Recursos de config/ y data/ cargados.")

    def _read_json(self, file_path, default):
        if not os.path.exists(file_path):
            print(f"⚠️ Aviso: {file_path} no encontrado.")
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error en JSON {file_path}: {e}")
            return default

    def get_env(self, key, default=None):
        return os.getenv(key, default)
    
    # El decorador @property permite llamar a este método como si fuera un atributo (self.system_prompt)
    # Esto centraliza la construcción de la personalidad de Kimera.
    @property
    def system_prompt(self):
        """
        Ensamblador de Personalidad:
        Combina las reglas técnicas (system_rules) con las reglas de rol (personality_rules).
        Sirve para que el Processor.py no tenga que saber cómo se estructuran las reglas en el JSON;
        simplemente solicita el prompt final listo para ser enviado a la IA.
        """
        # Extraemos las listas del config.json. Usamos un fallback [] por seguridad de QA.
        rules = self.config.get("system_rules", [])
        personality = self.config.get("personality_rules", [])
        
        # Unimos ambas listas en un bloque sólido de texto para el System Message de la IA.
        full_prompt = " ".join(rules + personality)
        
        # Fallback crítico: Si no hay reglas definidas, el bot no se queda mudo ni sin identidad.
        return full_prompt if full_prompt else "Eres Kimera, una VTuber quimera creada por Klumsy Healer."