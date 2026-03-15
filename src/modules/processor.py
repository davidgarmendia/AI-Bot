import re
import asyncio
from openai import OpenAI

class KimeraProcessor:
    def __init__(self, loader):
        self.loader = loader
        self.ia_url = "http://localhost:1234/v1"
        self.client_ai = OpenAI(base_url=self.ia_url, api_key="lm-studio")

        self.system_prompt = "Eres Kim, una asistente de stream divertida, breve y sarcástica. Responde en español, máximo dos frases."
        self.restricted_terms = [] 

    def humanizar_texto(self, texto):
        reemplazos = {" XD": " equis dé", " LOL": " lool", " :)": " ¡jeje!", "www.": " u ve doble punto ", " ID": " i dé"}
        for original, nuevo in reemplazos.items():
            texto = texto.replace(original, nuevo)
        return texto

    def _aplicar_filtros(self, texto):
        if not self.restricted_terms: return texto
        for palabra in self.restricted_terms:
            pattern = re.compile(rf'\b{re.escape(palabra)}\b', re.IGNORECASE)
            texto = pattern.sub("****", texto)
        return texto

    async def generate_response(self, usuario, mensaje):
        mensaje_limpio = self._aplicar_filtros(mensaje)
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: self.client_ai.chat.completions.create(
                model="meta-llama-3-8b-instruct",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{usuario} dice: {mensaje_limpio}"}
                ],
                temperature=0.7,
                max_tokens=80,
                stop=["\n", f"{usuario}:", "Usuario:"]
            ))
            
            respuesta_ia = res.choices[0].message.content.strip()
            respuesta_final = self.humanizar_texto(self._aplicar_filtros(respuesta_ia))
            
            print(f"🤖 [Kim Responde]: {respuesta_final}")
            return respuesta_final
        except Exception as e:
            print(f"❌ Error en KimeraProcessor: {e}")
            return "Mis circuitos se cruzaron, ¿qué decías?"