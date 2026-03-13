import pytchat
import asyncio
import httpx  # Necesitaremos esta librería para un scraping más robusto
import re
from youtubesearchpython import __future__ as LiveStream

class YouTubeManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        # Recomendación: Usa el ID que empieza por UC... en tu .env
        self.channel_identifier = self.loader.get_env("YOUTUBE_CHANNEL_ID")
        self.processor = processor
        self.tts = tts
        self.chat = None
        self.is_running = True

    async def get_live_id(self):
        """
        QA Mejorado: Intenta múltiples métodos para encontrar el ID del directo.
        """
        # Método 1: Intentar con la URL /live y Regex (Más rápido y confiable)
        try:
            url = f"https://www.youtube.com/{self.channel_identifier}/live"
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.31"}
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                # Buscamos el ID del video en el código fuente de la página
                match = re.search(r'videoIds":\["([^"]+)"\]', response.text)
                if match:
                    return match.group(1)
                
                # Segundo intento por si el formato cambia
                match = re.search(r'canonical" href="https://www.youtube.com/watch\?v=([^"]+)"', response.text)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"⚠️ YouTube Regex Falló: {e}")

        # Método 2: Fallback a LiveStream (Tu método original)
        try:
            target_url = f"https://www.youtube.com/{self.channel_identifier}/live"
            video = await LiveStream.Video.getInfo(target_url)
            if video and 'id' in video:
                return video['id']
        except:
            return None
            
        return None

    async def start(self):
        print(f"📡 YouTube: Iniciando monitoreo para {self.channel_identifier}")

        while self.is_running:
            # Intentamos obtener el ID
            video_id = await self.get_live_id()

            if not video_id:
                print(f"☁️ YouTube: No se detecto stream activo en {self.channel_identifier}. Reintentando en 30s...")
                await asyncio.sleep(30)
                continue

            try:
                # La librería pytchat es síncrona, pero la envolvemos para no bloquear
                self.chat = pytchat.create(video_id=video_id)
                print(f"✅ YouTube: ¡Conectado al chat! (Video ID: {video_id})")

                while self.chat.is_alive():
                    # Usamos un bucle no bloqueante para procesar mensajes
                    data = self.chat.get()
                    for c in data.sync_items():
                        usuario = c.author.name
                        mensaje = c.message
                        
                        print(f"💬 [YouTube] {usuario}: {mensaje}")

                        # Lanzamos la respuesta como una tarea para no detener la escucha
                        asyncio.create_task(self._process_message(usuario, mensaje))

                    await asyncio.sleep(1) # Respiro para el procesador

            except Exception as e:
                print(f"❌ Error en conexión de chat YouTube: {e}")
                await asyncio.sleep(10)

    async def _process_message(self, usuario, mensaje):
        """Tarea separada para procesar mensajes sin bloquear el chat."""
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