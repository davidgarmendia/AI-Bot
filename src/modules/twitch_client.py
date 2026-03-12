from twitchio.ext import commands

class TwitchManager(commands.Bot):
    def __init__(self, loader, processor, tts):
        # 1. Recuperamos credenciales del Loader
        self.loader = loader
        self.token = self.loader.get_env("TWITCH_TOKEN")
        self.channel = self.loader.get_env("TWITCH_CHANNEL")
        self.prefix = "?" # Prefijo para comandos técnicos si los necesitas

        # 2. Conectamos con los otros módulos
        self.processor = processor
        self.tts = tts

        # 3. Inicializamos el bot de TwitchIO
        super().__init__(
            token=self.token,
            prefix=self.prefix,
            initial_channels=[self.channel]
        )

    async def event_ready(self):
        """QA: Confirmación de conexión exitosa."""
        print(f"📡 Twitch: Conectado como {self.nick}")
        print(f"📺 Escuchando el canal: {self.channel}")

    async def event_message(self, data):
        """
        Este es el 'Oído'. Filtra y procesa cada mensaje del chat.
        """
        # Ignorar mensajes del propio bot para evitar bucles infinitos
        if data.author is not None and data.author.name.lower() == self.nick.lower():
            return

        usuario = data.author.name
        contenido = data.content

        print(f"💬 [Twitch] {usuario}: {contenido}")

        # REGLA DE LECTURA TOTAL: Enviamos todo al cerebro de Kimera
        try:
            # 1. El Cerebro genera la respuesta
            respuesta = await self.processor.generate_response(usuario, contenido)
            
            # 2. La Voz la pone en la cola de audio
            if respuesta:
                await self.tts.agregar_a_cola(respuesta)
                
        except Exception as e:
            print(f"❌ Error al procesar mensaje de Twitch: {e}")

        # Permitir que otros comandos sigan funcionando
        await self.handle_commands(data)