import re
import asyncio
from openai import OpenAI

class KimeraProcessor:
    def __init__(self, loader, memory):
        self.loader = loader
        self.memory = memory
        
        # Cargamos la URL desde el .env. Si no existe, usa localhost por defecto.
        self.ia_url = self.loader.get_env("IA_URL")
        self.client_ai = OpenAI(base_url=self.ia_url, api_key="lm-studio")

        self.system_prompt = "Eres Kim, una asistente de stream divertida, breve y sarcástica. Responde en español, máximo dos frases."
        self.restricted_terms = [] 

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
        
        # --- LÓGICA DE MEMORIA SEGURA ---
        # 1. Recuperamos el contexto (si no hay, devuelve lista vacía [])
        contexto_previo = self.memory.get_context(usuario)
        
        # 2. Iniciamos la lista de mensajes con el System Prompt
        mensajes_ia = [{"role": "system", "content": self.system_prompt}]
        
        # 3. Insertamos el historial SOLO si tiene contenido
        if contexto_previo and len(contexto_previo) > 0:
            for interaccion in contexto_previo:
                # Verificamos que la estructura del JSON sea correcta
                if 'user' in interaccion and 'bot' in interaccion:
                    mensajes_ia.append({"role": "user", "content": interaccion['user']})
                    mensajes_ia.append({"role": "assistant", "content": interaccion['bot']})
        
        # 4. Añadimos la interacción actual
        mensajes_ia.append({"role": "user", "content": f"{usuario} dice: {mensaje_limpio}"})

        try:
            # Ejecución asíncrona para no bloquear el bot mientras la IA piensa
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: self.client_ai.chat.completions.create(
                model="meta-llama-3-8b-instruct",
                messages=mensajes_ia,
                temperature=0.7,
                max_tokens=80,
                stop=["\n", f"{usuario}:", "Usuario:"]
            ))
            
            respuesta_ia = res.choices[0].message.content.strip()
            
            # Limpieza y humanización de la respuesta
            respuesta_final = self.humanizar_texto(self._aplicar_filtros(respuesta_ia))
            
            # --- GUARDAR EN MEMORIA ---
            # Guardamos para que en el siguiente mensaje Kim sepa qué respondió
            self.memory.save_interaction(usuario, mensaje_limpio, respuesta_final)
            
            print(f"🤖 [Kim Responde]: {respuesta_final}")
            return respuesta_final

        except Exception as e:
            # Si LM Studio está apagado o la URL está mal, Kim avisa con humor
            print(f"❌ Error en KimeraProcessor: {e}")
            return "Mis circuitos se cruzaron, ¿podrías repetirlo?"