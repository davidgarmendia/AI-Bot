import asyncio
from twitchio.ext import commands

class TwitchManager(commands.Bot):
    def __init__(self, loader, processor, tts):
        self.loader = loader
        
        # Cargamos los datos de forma segura
        token = self.loader.get_env("TWITCH_TOKEN").strip()
        channel = self.loader.get_env("TWITCH_CHANNEL").strip()
        client_id = self.loader.get_env("TWITCH_CLIENT_ID").strip()
        client_secret = self.loader.get_env("TWITCH_CLIENT_SECRET").strip()
        account_id = self.loader.get_env("TWITCH_ACCOUNT_ID").strip()
        
        self.channel = channel
        self.prefix = "?"
        self.processor = processor
        self.tts = tts

        super().__init__(
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=account_id,
            prefix=self.prefix,
            initial_channels=[self.channel]
        )

    async def event_ready(self):
        print(f"==================================================")
        print(f"📡 Twitch: CONEXIÓN SEGURA ESTABLECIDA")
        print(f"📺 Canal activo: {self.channel}")
        print(f"==================================================")

    async def event_error(self, error, data=None):
        print(f"⚠️ Twitch Error: La conexión fue rechazada o falló. Revisa tu archivo .env.")

    async def event_message(self, data):
        # Ignorar mensajes del propio bot
        if data.author is None or data.author.name.lower() == self.channel.lower():
            return

        # --- ARREGLO DE NICK (Display Name) ---
        # data.author.display_name mantiene las mayúsculas (ej: "Klumsy_TV" en vez de "klumsy_tv")
        usuario = data.author.display_name or data.author.name
        contenido = data.content
        
        # Imprimimos el log con el Nick real
        print(f"💬 [Twitch] {usuario}: {contenido}")

        # Filtro de activación (Solo responde si mencionan a Kim o Kimera)
        trigger_words = ["kim", "kimera"]
        if any(word in contenido.lower() for word in trigger_words):
            try:
                # Procesar con timeout
                respuesta = await asyncio.wait_for(
                    self.processor.generate_response(usuario, contenido), 
                    timeout=8.0
                )
                
                if respuesta:
                    # Log de confirmación de voz
                    print(f"🔊 [Twitch] Enviando respuesta de {usuario} a voz...")
                    await self.tts.agregar_a_cola(respuesta)
                    
            except asyncio.TimeoutError:
                print(f"⏳ [Twitch] Tiempo de espera agotado para la respuesta a {usuario}")
            except Exception as e:
                print(f"❌ Error procesando mensaje de Twitch: {e}")

        await self.handle_commands(data)