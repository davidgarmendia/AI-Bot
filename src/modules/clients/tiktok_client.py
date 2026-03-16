import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

class TikTokManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        self.username = self.loader.get_env("TIKTOK_NICKNAME")
        self.processor = processor
        self.tts = tts
        
        # Inicializamos el cliente
        self.client = TikTokLiveClient(unique_id=self.username)

        # Registramos los eventos
        self.client.on(ConnectEvent)(self.on_connect)
        self.client.on(CommentEvent)(self.on_comment)

    async def on_connect(self, event: ConnectEvent):
        print(f"📡 [TikTok] CONEXIÓN EXITOSA: Escuchando el live de {self.username}")

    async def on_comment(self, event: CommentEvent):
        # Identificar al usuario
        usuario = event.user.nickname or event.user.unique_id
        mensaje = event.comment
        
        # Filtro de activación: Kim solo responde si la mencionan
        trigger_words = ["kim", "kimera"]
        if any(word in mensaje.lower() for word in trigger_words):
            print(f"💬 [TikTok] {usuario}: {mensaje}")
            
            try:
                # Generamos respuesta con la IA
                respuesta = await self.processor.generate_response(usuario, mensaje)
                
                if respuesta:
                    print(f"🔊 [TikTok] Enviando respuesta a la cola de voz...")
                    await self.tts.agregar_a_cola(respuesta)
                    
            except Exception as e:
                print(f"❌ Error en procesamiento TikTok: {e}")

    async def run(self):
        """Arranca TikTok sin bloquear el resto del sistema"""
        if not self.username:
            print("⚠️ TikTok: TIKTOK_NICKNAME no definido en el .env")
            return
        
        # Lanzamos la conexión como una tarea de fondo
        # Esto evita que el RATE_LIMIT congele a Twitch o al TTS
        asyncio.create_task(self._connect_safely())

    async def _connect_safely(self):
        """Maneja la conexión real y los errores de rate limit"""
        try:
            print(f"⏳ [TikTok] Intentando conectar con @{self.username}...")
            await self.client.start()
        except Exception as e:
            if "RATE_LIMIT" in str(e).upper():
                print(f"🛑 [TikTok] BLOQUEO TEMPORAL (Rate Limit).")
                print(f"👉 Kim funcionará en Twitch, pero en TikTok hay que esperar 15 min.")
            else:
                print(f"❌ [TikTok] Error de conexión: {e}")