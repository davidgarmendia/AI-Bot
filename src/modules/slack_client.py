import asyncio
from slack_bolt.app import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

class SlackManager:
    def __init__(self, loader, processor, tts):
        self.loader = loader
        self.processor = processor
        self.tts = tts
        
        # Cargamos los tokens que ya tienes en el .env
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
            # Obtenemos el texto y el ID del usuario
            user_id = event.get("user")
            text = event.get("text")
            
            print(f"💬 [Slack] Mención recibida de {user_id}: {text}")

            # Función interna para procesar el mensaje con la IA
            async def process_slack_msg():
                # Limpiamos el texto (quitamos el @Kim del mensaje)
                clean_text = text.split(">")[-1].strip()
                
                # Kim genera la respuesta (le pasamos un nombre genérico o el ID)
                respuesta = await self.processor.generate_response(f"Jefe de Slack", clean_text)
                
                if respuesta:
                    # 1. Kim responde en Slack (en un hilo para no ensuciar el canal)
                    say(text=respuesta, thread_ts=event.get("ts"))
                    
                    # 2. OPCIONAL: Descomenta la línea de abajo si quieres que Kim hable en el stream
                    # await self.tts.agregar_a_cola(respuesta)

            # Lanzamos la tarea asíncrona correctamente desde el hilo de Slack
            asyncio.run_coroutine_threadsafe(process_slack_msg(), asyncio.get_event_loop())

    async def run(self):
        """Arranca el Socket Mode de Slack"""
        if not self.app_token: return
        
        print("🔌 Slack: Conexión establecida en modo privado (Socket Mode).")
        
        # Ejecutamos el handler en un hilo separado para que no bloquee el resto del bot
        handler = SocketModeHandler(self.app, self.app_token)
        await asyncio.to_thread(handler.connect)