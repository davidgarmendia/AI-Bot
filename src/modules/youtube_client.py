import pytchat
import asyncio
import httpx
import re
from youtubesearchpython import __future__ as LiveStream

class YouTubeManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        # ID del canal (UC...) o handle (@Nombre)
        self.channel_identifier = self.loader.get_env("YOUTUBE_CHANNEL_ID")
        self.processor = processor
        self.tts = tts
        self.chat = None
        self.is_running = True

    async def get_live_id(self):
        """
        Busca el ID del video en vivo actualmente.
        """
        if not self.channel_identifier:
            print("❌ YouTube Error: No se configuró YOUTUBE_CHANNEL_ID en el .env")
            return None

        # Limpieza de URL en caso de que el ID venga con espacios
        identifier = self.channel_identifier.strip()
        url = f"https://www.youtube.com/{identifier}/live"
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                # Intentar encontrar el videoId en el script de la página
                match = re.search(r'videoIds":\["([^"]+)"\]', response.text)
                if match:
                    return match.group(1)
                
                # Intento alternativo por URL canónica
                match = re.search(r'canonical" href="https://www.youtube.com/watch\?v=([^"]+)"', response.text)
                if match:
                    return match.group(1)
                    
        except Exception as e:
            print(f"⚠️ YouTube Scraping Falló: {e}")

        # Fallback a la librería LiveStream
        try:
            video = await LiveStream.Video.getInfo(url)
            if video and 'id' in video:
                return video['id']
        except:
            pass
            
        return None

    async def start(self):
        print(f"📡 YouTube: Iniciando monitoreo para {self.channel_identifier}")

        while self.is_running:
            # PRIORIDAD: 1. ID manual del .env | 2. Búsqueda automática
            manual_id = self.loader.get_env("YOUTUBE_VIDEO_ID")
            video_id = manual_id if manual_id else await self.get_live_id()

            if not video_id:
                print(f"☁️ YouTube: No se detectó stream activo en {self.channel_identifier}. Reintentando en 30s...")
                await asyncio.sleep(30)
                continue

            try:
                # Inicializar el chat
                self.chat = pytchat.create(video_id=video_id)
                
                if self.chat.is_alive():
                    print(f"✅ YouTube: ¡Conectado al chat! (Video ID: {video_id})")
                else:
                    # Si pytchat no puede conectar, el ID podría ser inválido
                    print(f"⚠️ YouTube: El ID {video_id} no parece tener un chat activo.")
                    await asyncio.sleep(20)
                    continue

                while self.chat.is_alive() and self.is_running:
                    data = self.chat.get()
                    for c in data.sync_items():
                        usuario = c.author.name
                        mensaje = c.message
                        
                        print(f"💬 [YouTube] {usuario}: {mensaje}")

                        # Procesar respuesta de Kim
                        asyncio.create_task(self._process_message(usuario, mensaje))

                    await asyncio.sleep(1) # Evita saturar el procesador

            except Exception as e:
                print(f"❌ Error en conexión de chat YouTube: {e}")
                await asyncio.sleep(10)

    async def _process_message(self, usuario, mensaje):
        """Genera respuesta usando el procesador modular y la envía al TTS."""
        try:
            respuesta = await self.processor.generate_response(usuario, mensaje)
            if respuesta:
                await self.tts.agregar_a_cola(respuesta)
        except Exception as ai_err:
            print(f"❌ Error en IA (YouTube): {ai_err}")

    def stop(self):
        self.is_running = False
        if self.chat:
            self.chat.terminate()
        print("🔒 YouTube: Cliente detenido.")