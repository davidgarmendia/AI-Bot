import asyncio
from slack_bolt.app import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

class SlackManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        self.processor = processor
        self.tts = tts
        
        # Capturamos el bucle de eventos actual
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()
        
        # Cargamos los tokens del .env
        self.bot_token = self.loader.get_env("SLACK_BOT_TOKEN")
        self.app_token = self.loader.get_env("SLACK_APP_TOKEN")
        
        if not self.bot_token or not self.app_token:
            print("⚠️ Slack: Faltan tokens en el .env")
            return

        # Inicializamos la App de Slack
        self.app = App(token=self.bot_token)
        self._register_events()

    def _register_events(self):
        """Registro de eventos para escuchar a Slack"""
        
        @self.app.event("app_mention")
        def handle_mentions(event, say):
            user_id = event.get("user")
            text = event.get("text", "")
            thread_ts = event.get("ts")

            # --- OBTENER EL NICK REAL ---
            try:
                user_info = self.app.client.users_info(user=user_id)
                profile = user_info['user']['profile']
                user_nick = profile.get('display_name') or profile.get('real_name') or user_id
            except Exception as e:
                print(f"⚠️ No se pudo obtener el nick: {e}")
                user_nick = "Usuario"

            print(f"💬 [Slack] Mención de {user_nick}") 

            async def process_slack_msg():
                try:
                    # Limpiamos el texto
                    clean_text = text.split(">")[-1].strip()
                    if not clean_text:
                        clean_text = "Hola"

                    # Generamos la respuesta con la IA
                    respuesta = await self.processor.generate_response(user_nick, clean_text)
                    
                    if respuesta:
                        # --- NUEVA LÓGICA DE SINCRONIZACIÓN ---
                        
                        # 1. Primero procesamos el audio y ESPERAMOS a que termine de sonar
                        print(f"🔊 Generando audio y esperando reproducción...")
                        # IMPORTANTE: Usamos 'reproducir_y_esperar' del nuevo TTSEngine
                        await self.tts.reproducir_y_esperar(respuesta)
                        
                        # 2. Una vez que Kim terminó de hablar, enviamos el texto a Slack
                        print(f"✅ Audio finalizado. Enviando texto a Slack...")
                        say(text=respuesta, thread_ts=thread_ts)
                
                except Exception as e:
                    print(f"❌ Error procesando mensaje de Slack: {e}")

            # Ejecución en el loop principal
            self.loop.call_soon_threadsafe(lambda: asyncio.create_task(process_slack_msg()))

    async def run(self):
        """Arranca el Socket Mode de Slack"""
        if not self.app_token: 
            return
        
        print("🔌 Slack: Conexión activa.")
        handler = SocketModeHandler(self.app, self.app_token)
        await asyncio.to_thread(handler.connect)