from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

class TikTokManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        self.username = self.loader.get_env("TIKTOK_NICKNAME")
        self.processor = processor
        self.tts = tts
        
        # Inicializamos el cliente (sin el @ si ya lo manejas en el env)
        self.client = TikTokLiveClient(unique_id=self.username)

        # Registramos los eventos
        self.client.on(ConnectEvent)(self.on_connect)
        self.client.on(CommentEvent)(self.on_comment)

    async def on_connect(self, event: ConnectEvent):
        print(f"📡 TikTok: Conectado al live de {self.username}")

    async def on_comment(self, event: CommentEvent):
        usuario = event.user.nickname
        mensaje = event.comment
        
        trigger_words = ["kim", "kimera"]
        if any(word in mensaje.lower() for word in trigger_words):
            print(f"💬 [TikTok] {usuario}: {mensaje}")
            
            try:
                respuesta = await self.processor.generate_response(usuario, mensaje)
                if respuesta:
                    await self.tts.agregar_a_cola(respuesta)
            except Exception as e:
                print(f"❌ Error en procesamiento TikTok: {e}")

    async def run(self):
        """Método unificado para el arranque"""
        if not self.username:
            print("⚠️ TikTok: TIKTOK_NICKNAME no definido.")
            return
        
        try:
            await self.client.start()
        except Exception as e:
            print(f"❌ Error al conectar con TikTok: {e}")