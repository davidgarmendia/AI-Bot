from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

class TikTokManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        self.username = self.loader.get_env("TIKTOK_NICKNAME")
        self.processor = processor
        self.tts = tts
        
        # Inicializamos el cliente
        self.client = TikTokLiveClient(unique_id=f"@{self.username}")

        # Registramos los eventos
        self.client.on(ConnectEvent)(self.on_connect)
        self.client.on(CommentEvent)(self.on_comment)

    async def on_connect(self, event: ConnectEvent):
        print(f"📡 TikTok: Conectado al live de @{self.username}")

    async def on_comment(self, event: CommentEvent):
        usuario = event.user.nickname
        mensaje = event.comment
        
        # --- LÓGICA DE FILTRO POR KEYWORD ---
        # Solo responde si mencionan a "Kim" o "Kimera" (insensible a mayúsculas)
        trigger_words = ["kim", "kimera"]
        if any(word in mensaje.lower() for word in trigger_words):
            print(f"💬 [TikTok] {usuario} (Trigger): {mensaje}")
            
            try:
                # El flujo de siempre: IA -> TTS
                respuesta = await self.processor.generate_response(usuario, mensaje)
                if respuesta:
                    await self.tts.agregar_a_cola(respuesta)
            except Exception as e:
                print(f"❌ Error en procesamiento TikTok: {e}")
        else:
            # QA: Log opcional para ver que el chat fluye sin responder a todo
            # print(f"☁️ [TikTok Skip] {usuario}: {mensaje}")
            pass

    async def start(self):
        """Inicia la conexión con TikTok."""
        if not self.username:
            print("⚠️ TikTok: TIKTOK_NICKNAME no definido.")
            return
        
        try:
            # TikTokLive es asíncrono pero tiene su propio manejo de bucle
            await self.client.start()
        except Exception as e:
            print(f"❌ Error al conectar con TikTok: {e}")