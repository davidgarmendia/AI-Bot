import asyncio
import sys
import os
import signal

# Agrega la carpeta actual al sistema para que Python encuentre los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.config_loader import ConfigLoader
from modules.processor import KimeraProcessor
from modules.tts_engine import TTSEngine
from modules.cli_parser import parse_arguments 
from modules.clients.slack_client import SlackManager
from modules.clients.tiktok_client import TikTokManager
from modules.clients.twitch_client import TwitchManager
from modules.clients.youtube_client import YouTubeManager

# --- FUNCIÓN DE APAGADO INSTANTÁNEO ---
def handle_exit(sig, frame):
    """Mata el proceso inmediatamente al recibir Ctrl+C."""
    # Usamos os._exit(0) para ignorar los hilos bloqueados de Slack
    print("\n👋 Kim se ha ido a dormir instantáneamente.")
    os._exit(0)

async def main():
    args = parse_arguments()
    
    # 1. CARGA DE CONFIGURACIÓN
    try:
        loader = ConfigLoader()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return

    bot_identity = loader.get_env("BOT_NAME", "Kimera")
    streamer_identity = loader.get_env("STREAMER_NAME", "Klumsy")

    # Banner visual de inicio
    print(f"\n{'='*50}\n      🤖 SISTEMA OPERATIVO {bot_identity.upper()} V2.0\n{'='*50}\n")

    # 2. INICIALIZACIÓN DE MOTORES (IA y Voz)
    processor = KimeraProcessor(loader)
    tts = TTSEngine(loader)
    
    tasks = []
    # El worker del TTS siempre debe estar corriendo para procesar la cola de voz
    tasks.append(asyncio.create_task(tts.worker()))

    # 3. ACTIVACIÓN DE PLATAFORMAS SEGÚN ARGUMENTOS
    
    # Verifica si vamos a usar Slack
    if args.all or getattr(args, 'slack', False):
        sm = SlackManager(loader, processor, tts)
        tasks.append(asyncio.create_task(sm.run()))

    # Verifica si vamos a usar Twitch
    if args.twitch or args.all:
        tm = TwitchManager(loader, processor, tts)
        tasks.append(asyncio.create_task(tm.start()))

    # Verifica si vamos a usar Youtube
    if args.youtube or args.all:
        ym = YouTubeManager(loader, processor, tts)
        tasks.append(asyncio.create_task(ym.start()))

    # Verifica si vamos a usar Tiktok
    if args.tiktok or args.all:
        tkm = TikTokManager(loader, processor, tts)
        tasks.append(asyncio.create_task(tkm.run()))

    # Saludo inicial de Kim
    await tts.reproducir_y_esperar(f"Sistema iniciado. Hola {streamer_identity}")
    print(f"🚀 {bot_identity.upper()} ESCUCHANDO.\n")

    # 4. EJECUCIÓN Y MANEJO DE CIERRE
    try:
        # Aquí el bot se queda corriendo "para siempre"
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        # Si por alguna razón asyncio detecta el cierre antes que signal
        handle_exit(None, None)
    finally:
        # Último recurso de limpieza
        for task in tasks: 
            task.cancel()
        os._exit(0)

if __name__ == "__main__":
    # REGISTRO DE SEÑAL DE CIERRE (Guillotina)
    # SIGINT es la señal que envía Control + C
    signal.signal(signal.SIGINT, handle_exit)

    # Ajuste para que asyncio funcione bien en Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        handle_exit(None, None)