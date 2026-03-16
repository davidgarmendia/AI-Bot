import asyncio
from twitchio.ext import commands

class TwitchManager(commands.Bot):
    def __init__(self, loader, processor, tts):
        self.loader = loader
        
        # Cargamos los datos de forma segura desde el ConfigLoader
        token = self.loader.get_env("TWITCH_TOKEN").strip()
        channel = self.loader.get_env("TWITCH_CHANNEL").strip()
        client_id = self.loader.get_env("TWITCH_CLIENT_ID").strip()
        client_secret = self.loader.get_env("TWITCH_CLIENT_SECRET").strip()
        account_id = self.loader.get_env("TWITCH_ACCOUNT_ID").strip()
        
        self.channel = channel
        self.prefix = "?"
        self.processor = processor
        self.tts = tts

        # Inicialización de la clase base de TwitchIO
        super().__init__(
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=account_id,
            prefix=self.prefix,
            initial_channels=[self.channel]
        )

    async def event_ready(self):
        """Se ejecuta cuando el bot se conecta a Twitch"""
        print(f"==================================================")
        print(f"📡 Twitch: CONEXIÓN SEGURA ESTABLECIDA")
        print(f"📺 Canal activo: {self.channel}")
        print(f"==================================================")

    async def event_error(self, error, data=None):
        """Maneja errores de conexión o de tokens"""
        print(f"⚠️ Twitch Error: La conexión fue rechazada o falló. Revisa tu archivo .env.")

    async def event_message(self, data):
        """Se ejecuta cada vez que alguien escribe en el chat"""
        # Ignorar mensajes del propio bot para evitar bucles infinitos
        if data.author is None or data.author.name.lower() == self.channel.lower():
            return

        # --- ARREGLO DE NICK (Display Name) ---
        # Usamos display_name para mantener las mayúsculas originales del usuario
        usuario = data.author.display_name or data.author.name
        contenido = data.content
        
        # Imprimimos el log en consola
        print(f"💬 [Twitch] {usuario}: {contenido}")

        # Filtro de activación (Kimera solo responde si la mencionan)
        trigger_words = ["kim", "kimera"]
        if any(word in contenido.lower() for word in trigger_words):
            try:
                # Procesar la respuesta con la IA
                respuesta = await asyncio.wait_for(
                    self.processor.generate_response(usuario, contenido), 
                    timeout=8.0
                )
                
                if respuesta:
                    # Log de confirmación para el motor de voz
                    print(f"🔊 [Twitch] Enviando respuesta de {usuario} a voz...")
                    await self.tts.agregar_a_cola(respuesta)
                    
            except asyncio.TimeoutError:
                print(f"⏳ [Twitch] Tiempo de espera agotado para la respuesta a {usuario}")
            except Exception as e:
                print(f"❌ Error procesando mensaje de Twitch: {e}")

        # Permite que otros comandos de TwitchIO funcionen si los hubiera
        await self.handle_commands(data)

    async def start(self):
        """
        Punto de entrada que llama bot.py.
        Llama al método start() de la clase base commands.Bot de forma asíncrona.
        """
        try:
            await super().start()
        except Exception as e:
            print(f"❌ Error crítico al iniciar TwitchManager: {e}")