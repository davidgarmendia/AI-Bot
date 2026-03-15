import asyncio
from slack_bolt.app import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

class SlackManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        self.processor = processor
        self.tts = tts
        
        # Guardamos una referencia al "bucle de eventos" principal del bot
        self.loop = asyncio.get_event_loop()
        
        # Cargamos los tokens del .env
        self.bot_token = self.loader.get_env("SLACK_BOT_TOKEN")
        self.app_token = self.loader.get_env("SLACK_APP_TOKEN")
        
        if not self.bot_token or not self.app_token:
            print("⚠️ Slack: Faltan tokens en el .env (SLACK_BOT_TOKEN o SLACK_APP_TOKEN)")
            return

        # Inicializamos la App de Slack
        self.app = App(token=self.bot_token)
        self._register_events()

    def _register_events(self):
        """Registro de eventos para escuchar a Slack"""
        
        @self.app.event("app_mention")
        def handle_mentions(event, say):
            user_id = event.get("user")
            text = event.get("text")
            
            print(f"💬 [Slack] Mención recibida de {user_id}: {text}")

            async def process_slack_msg():
                # Limpiamos el texto (quitamos el @Kim)
                clean_text = text.split(">")[-1].strip()
                
                # Kim genera la respuesta
                respuesta = await self.processor.generate_response(f"Jefe de Slack", clean_text)
                
                if respuesta:
                    # 1. Responde en el hilo de Slack
                    say(text=respuesta, thread_ts=event.get("ts"))
                    
                    # 2. ACTIVADO: Kim habla por AllTalk (female_03)
                    await self.tts.agregar_a_cola(respuesta)

            # Usamos self.loop para asegurarnos de que la tarea se ejecute en el lugar correcto
            asyncio.run_coroutine_threadsafe(process_slack_msg(), self.loop)

    async def run(self):
        """Arranca el Socket Mode de Slack sin bloquear el teclado"""
        if not self.app_token: return
        
        print("🔌 Slack: Conexión establecida en modo privado (Socket Mode).")
        
        # SocketModeHandler con .connect() no "secuestra" el Ctrl+C en Windows
        handler = SocketModeHandler(self.app, self.app_token)
        await asyncio.to_thread(handler.connect)