import re
import asyncio
from openai import OpenAI

class KimeraProcessor:
    def __init__(self, loader, memory):
        self.loader = loader
        self.memory = memory
        
        # Cargamos la URL desde el .env
        self.ia_url = self.loader.get_env("IA_URL")
        self.client_ai = OpenAI(base_url=self.ia_url, api_key="lm-studio")

        # CORRECCIÓN: Ahora usa la personalidad definida en personality.json
        self.system_prompt = self.loader.system_prompt
        # CORRECCIÓN: Cargamos los términos restringidos desde el loader
        self.restricted_terms = self.loader.restricted_terms 

    def humanizar_texto(self, texto):
        """Mejora la pronunciación del TTS para términos comunes"""
        reemplazos = {
            " XD": " equis dé", 
            " LOL": " lool", 
            " :)": " ¡jeje!", 
            "www.": " u ve doble punto ", 
            " ID": " i dé"
        }
        for original, nuevo in reemplazos.items():
            texto = texto.replace(original, nuevo)
        return texto

    def _aplicar_filtros(self, texto):
        """Filtra palabras prohibidas"""
        if not self.restricted_terms: 
            return texto
        for palabra in self.restricted_terms:
            pattern = re.compile(rf'\b{re.escape(palabra)}\b', re.IGNORECASE)
            texto = pattern.sub("****", texto)
        return texto

    async def generate_response(self, usuario, mensaje):
        mensaje_limpio = self._aplicar_filtros(mensaje)
        
        # 1. Recuperamos el contexto
        contexto_previo = self.memory.get_context(usuario)
        
        # 2. Iniciamos la lista de mensajes con el System Prompt actualizado
        mensajes_ia = [{"role": "system", "content": self.system_prompt}]
        
        # 3. Insertamos el historial
        if contexto_previo:
            for interaccion in contexto_previo:
                if 'user' in interaccion and 'bot' in interaccion:
                    mensajes_ia.append({"role": "user", "content": interaccion['user']})
                    mensajes_ia.append({"role": "assistant", "content": interaccion['bot']})
        
        # 4. Añadimos la interacción actual
        mensajes_ia.append({"role": "user", "content": f"{usuario} dice: {mensaje_limpio}"})

        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: self.client_ai.chat.completions.create(
                model="meta-llama-3-8b-instruct",
                messages=mensajes_ia,
                temperature=0.7,
                max_tokens=80,
                stop=["\n", f"{usuario}:", "Usuario:"]
            ))
            
            respuesta_ia = res.choices[0].message.content.strip()
            respuesta_final = self.humanizar_texto(self._aplicar_filtros(respuesta_ia))
            
            # Guardamos en memoria
            self.memory.save_interaction(usuario, mensaje_limpio, respuesta_final)
            
            print(f"🤖 [Kim Responde]: {respuesta_final}")
            return respuesta_final

        except Exception as e:
            print(f"❌ Error en KimeraProcessor: {e}")
            return "Mis circuitos se cruzaron, ¿podrías repetirlo?"