import asyncio
from twitchio.ext import commands

class TwitchManager(commands.Bot):
    def __init__(self, loader, processor, tts):
        self.loader = loader
        
        # Cargamos los datos de forma privada
        token = self.loader.get_env("TWITCH_TOKEN").strip()
        channel = self.loader.get_env("TWITCH_CHANNEL").strip()
        client_id = self.loader.get_env("TWITCH_CLIENT_ID").strip()
        client_secret = self.loader.get_env("TWITCH_CLIENT_SECRET").strip()
        account_id = self.loader.get_env("TWITCH_ACCOUNT_ID").strip()
        
        self.channel = channel
        self.prefix = "?"
        self.processor = processor
        self.tts = tts

        # Inicializamos sin guardar los tokens en self (más seguro)
        super().__init__(
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=account_id,
            prefix=self.prefix,
            initial_channels=[self.channel]
        )

    async def event_ready(self):
        # Mensaje limpio de seguridad
        print(f"==================================================")
        print(f"📡 Twitch: CONEXIÓN SEGURA ESTABLECIDA")
        print(f"📺 Canal activo: {self.channel}")
        print(f"==================================================")

    async def event_error(self, error, data=None):
        """Maneja errores sin revelar qué dato falló específicamente"""
        print(f"⚠️ Twitch Error: La conexión fue rechazada. Revisa tu archivo .env.")

    async def event_message(self, data):
        # Ignorar mensajes del propio bot
        if data.author is None or data.author.name.lower() == self.channel.lower():
            return

        usuario = data.author.name
        contenido = data.content
        
        # Solo imprimimos el chat
        print(f"💬 [Chat] {usuario}: {contenido}")

        try:
            # Procesar con timeout para evitar bloqueos
            respuesta = await asyncio.wait_for(
                self.processor.generate_response(usuario, contenido), 
                timeout=8.0
            )
            
            if respuesta:
                await self.tts.agregar_a_cola(respuesta)
                
        except Exception:
            # Error genérico para no ensuciar la consola en vivo
            print(f"❌ Kim tuvo un problema procesando el mensaje de {usuario}")

        await self.handle_commands(data)