import asyncio
from twitchio.ext import commands

class TwitchManager(commands.Bot):
    def __init__(self, loader, processor, tts):
        self.loader = loader
        
        token = self.loader.get_env("TWITCH_TOKEN", "").strip()
        channel = self.loader.get_env("TWITCH_CHANNEL", "theklumsyhealer").strip().lower()
        client_id = self.loader.get_env("TWITCH_CLIENT_ID", "").strip()
        client_secret = self.loader.get_env("TWITCH_CLIENT_SECRET", "").strip()
        account_id = self.loader.get_env("TWITCH_ACCOUNT_ID", "").strip()
        
        self.channel_name = channel
        self.prefix = "?"
        self.processor = processor
        self.tts = tts

        super().__init__(
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            bot_id=account_id,
            prefix=self.prefix,
            initial_channels=[self.channel_name]
        )

    async def event_ready(self):
        print(f"\n" + "="*50)
        print(f"📡 Twitch: CONEXIÓN ESTABLECIDA")
        print(f"📺 Canal: {self.channel_name}")
        print(f"🤖 Kim está lista y escuchando chat...")
        print(f"="*50 + "\n")

    async def event_message(self, message):
        if message.echo:
            return

        usuario = "Desconocido"
        if message.author:
            usuario = message.author.display_name or message.author.name
        
        contenido = message.content
        print(f"💬 [Twitch Chat] {usuario}: {contenido}")

        trigger_words = ["kim", "kimera"]
        mencionada = any(word in contenido.lower() for word in trigger_words)
        
        es_streamer = False
        if message.author:
            es_streamer = message.author.name.lower() == self.channel_name.lower()

        if mencionada or es_streamer:
            print(f"✨ Kim detectó un mensaje para responder...")
            # Lanzamos la respuesta como tarea para no bloquear el chat
            asyncio.create_task(self.responder_con_voz(usuario, contenido))

        await self.handle_commands(message)

    async def responder_con_voz(self, usuario, contenido):
        try:
            respuesta = await self.processor.generate_response(usuario, contenido)
            
            if respuesta:
                # CORRECCIÓN: Quitamos el timeout. 
                # Solo lo añadimos a la cola y dejamos que el TTS Worker lo gestione.
                await self.tts.agregar_a_cola(respuesta)
                print(f"🔊 [Voz] Respuesta enviada a la cola de reproducción.")

        except Exception as e:
            print(f"❌ [Twitch Manager] Error al procesar respuesta: {e}")

    async def start(self):
        await super().start()