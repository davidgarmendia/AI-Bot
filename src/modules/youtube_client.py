import pytchat
import asyncio
from youtubesearchpython import __future__ as LiveStream

class YouTubeManager:
    def __init__(self, loader, processor, tts):
        """
        Constructor del cliente de YouTube.
        Inyecta el loader para config, el processor para la IA y el tts para la voz.
        """
        self.loader = loader
        # Puedes usar el ID (UC...) o el Handle (@KlumsyHealer) en el .env
        self.channel_identifier = self.loader.get_env("YOUTUBE_CHANNEL_ID")
        self.processor = processor
        self.tts = tts
        self.chat = None
        self.is_running = True

    async def get_live_id(self):
        """
        QA: Busca dinamicamente el ID del video que esta en directo.
        Esto evita tener que editar el .env en cada stream.
        """
        try:
            # Construimos la URL de 'live' del canal que siempre redirige al directo actual
            target_url = f"https://www.youtube.com/{self.channel_identifier}/live"
            
            # Buscamos la informacion del video en esa URL
            video = await LiveStream.Video.getInfo(target_url)
            
            if video and 'id' in video:
                return video['id']
        except Exception as e:
            # Si no hay directo, la libreria lanzara una excepcion o no encontrara el ID
            return None
        return None

    async def start(self):
        """
        Orquestador del cliente de YouTube. 
        Maneja la reconexion automatica si no encuentra un stream al inicio.
        """
        print(f"📡 YouTube: Iniciando monitoreo para {self.channel_identifier}")

        while self.is_running:
            video_id = await self.get_live_id()

            if not video_id:
                # Si no hay directo, esperamos 30 segundos antes de volver a preguntar
                # Esto ahorra recursos y evita bloqueos de IP por parte de YouTube
                print(f"☁️ YouTube: No se detecto stream activo en {self.channel_identifier}. Reintentando en 30s...")
                await asyncio.sleep(30)
                continue

            try:
                # Creamos la conexion al chat de YouTube
                self.chat = pytchat.create(video_id=video_id)
                print(f"✅ YouTube: ¡Conectado al chat! (Video ID: {video_id})")

                # Bucle de escucha mientras el chat este vivo
                while self.chat.is_alive():
                    # get().sync_items() obtiene los mensajes nuevos
                    for c in self.chat.get().sync_items():
                        usuario = c.author.name
                        mensaje = c.message
                        
                        print(f"💬 [YouTube] {usuario}: {mensaje}")

                        # Flujo Core: Procesar con IA y enviar a Cola de Voz
                        try:
                            respuesta = await self.processor.generate_response(usuario, mensaje)
                            if respuesta:
                                await self.tts.agregar_a_cola(respuesta)
                        except Exception as ai_err:
                            print(f"❌ Error en IA (YouTube): {ai_err}")

                    # Espera corta para no saturar el hilo
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"❌ Error en conexion de chat YouTube: {e}")
                await asyncio.sleep(10) # Espera antes de intentar reconectar todo

    def stop(self):
        """Metodo de apagado seguro."""
        self.is_running = False
        if self.chat:
            self.chat.terminate()
        print("🔒 YouTube: Cliente detenido.")