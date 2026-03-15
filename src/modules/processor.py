import re
from openai import OpenAI

class KimeraProcessor:
    def __init__(self, loader):
        """
        Recibe el objeto 'loader' que ya tiene la configuración cargada.
        """
        self.loader = loader
        # Configuramos el cliente de la IA (LM Studio)
        self.client_ai = OpenAI(
            base_url="http://localhost:1234/v1", 
            api_key="lm-studio"
        )
    async def generate_response(self, usuario, mensaje):
        # 1. Obtener respuesta de la IA (LM Studio / OpenAI)
        respuesta = await self.llm.ask(usuario, mensaje) 

        # 2. Aplicar "Filtro de Humanización"
        respuesta = self.humanizar_texto(respuesta)
        
        return respuesta

    def humanizar_texto(self, texto):
        # Reemplazos rápidos para que suene mejor
        reemplazos = {
            " XD": " equis dé",
            " LOL": " lool",
            " :)": " ¡jeje!",
            "www.": " u ve doble, u ve doble, u ve doble punto ",
            " ID": " i dé"
        }
        
        for original, nuevo in reemplazos.items():
            texto = texto.replace(original, nuevo)
            
        # Forzar una pausa tras el saludo inicial
        if "¡Hola!" in texto:
            texto = texto.replace("¡Hola!", "¡Hola!... ")
            
        return texto
        
        # Cargamos el prompt del sistema y los términos restringidos
        self.system_prompt = self.loader.system_prompt
        self.restricted_terms = self.loader.restricted_terms

    def _aplicar_filtros(self, texto):
        """
        QA Check: Revisa si el mensaje contiene palabras prohibidas 
        antes de enviarlo a la IA o al TTS.
        """
        for palabra in self.restricted_terms:
            # Usamos regex para encontrar palabras completas e ignorar mayúsculas
            pattern = re.compile(rf'\b{re.escape(palabra)}\b', re.IGNORECASE)
            texto = pattern.sub("****", texto)
        return texto

    async def generate_response(self, usuario, mensaje):
        """
        Encuentro entre el mensaje del usuario y la lógica de la IA.
        """
        # 1. Filtramos el mensaje de entrada (Seguridad)
        mensaje_limpio = self._aplicar_filtros(mensaje)
        
        try:
            # 2. Petición a LM Studio
            res = self.client_ai.chat.completions.create(
                model="meta-llama-3-8b-instruct",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"{usuario} dice: {mensaje_limpio}"}
                ],
                timeout=15
            )
            
            respuesta_ia = res.choices[0].message.content
            
            # 3. Filtramos la respuesta de la IA (Doble Seguridad)
            respuesta_final = self._aplicar_filtros(respuesta_ia)
            
            # 4. Manejo de etiquetas especiales (como el tag de [PREGUNTA])
            if "[PREGUNTA]" in respuesta_final:
                print(f"🤔 Kim tiene una duda sobre lo que dijo {usuario}")
                # Aquí podrías disparar lógica adicional en el futuro
            
            return respuesta_final

        except Exception as e:
            print(f"❌ Error en el procesador de IA: {e}")
            return "¡Uy! Mis orejas de quimera se hicieron nudo, ¿puedes repetir eso?"