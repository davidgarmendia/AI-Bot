import json
import os
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self):
        # Localiza la raíz del proyecto (sube 2 niveles desde src/modules)
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        load_dotenv(os.path.join(self.base_dir, ".env"))

        # --- DICCIONARIO DE RUTAS CENTRALIZADO ---
        # Si alguna vez mueves un archivo, solo lo cambias aquí.
        self.paths = {
            "settings": os.path.join(self.base_dir, "config", "settings.json"),
            "personality": os.path.join(self.base_dir, "config", "personality.json"),
            "dialogues": os.path.join(self.base_dir, "data", "dialogues.json"),
            "restricted": os.path.join(self.base_dir, "data", "restricted_terminology.json")
        }

        # Carga inicial de datos
        self.settings = self._read_json(self.paths["settings"], {})
        self.personality = self._read_json(self.paths["personality"], {"rules": []})
        self.dialogues = self._read_json(self.paths["dialogues"], {"saludos": {}})
        
        # Cargamos la blacklist de términos restringidos
        restricted_data = self._read_json(self.paths["restricted"], {"blacklist": []})
        self.restricted_terms = restricted_data.get("blacklist", [])
        
        print("✅ ConfigLoader V2: Recursos de config/ y data/ vinculados correctamente.")

    def _read_json(self, file_path, default):
        """Lector genérico y seguro para cualquier archivo JSON."""
        if not os.path.exists(file_path):
            print(f"⚠️ Aviso: No se encontró {file_path}. Usando valores por defecto.")
            return default
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error crítico procesando JSON en {file_path}: {e}")
            return default

    def get_env(self, key, default=None):
        """Obtiene variables del archivo .env"""
        return os.getenv(key, default)

    def get_dialogue(self, categoria, clave):
        """Obtiene frases predefinidas desde data/dialogues.json"""
        return self.dialogues.get(categoria, {}).get(clave, "¡Sistema en línea!")

    def get_phonetic_replacements(self):
        """Obtiene las reglas de pronunciación guardadas en config/settings.json"""
        return self.settings.get("phonetic_replacements", {})

    @property
    def system_prompt(self):
        """
        Ensamblador de Personalidad:
        Une todas las reglas de config/personality.json en un bloque sólido para la IA.
        """
        # Intentamos obtener 'rules' (el nuevo estándar) o las llaves viejas por si acaso
        rules = self.personality.get("rules", [])
        if not rules:
            # Soporte de transición por si aún usas los nombres viejos en el JSON
            rules = self.personality.get("system_rules", []) + self.personality.get("personality_rules", [])
        
        full_prompt = " ".join(rules)
        
        # Fallback de seguridad si el archivo está vacío
        if not full_prompt:
            return "Eres Kim, una asistente carismática creada por Klumsy Healer."
        
        return full_prompt