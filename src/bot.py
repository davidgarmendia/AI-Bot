import asyncio
import sys
import os
import signal

# Carpeta actual al sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.config_loader import ConfigLoader
from modules.processor import KimeraProcessor
from modules.tts_engine import TTSEngine
from modules.cli_parser import parse_arguments 
from modules.memory_manager import MemoryManager # <--- NUEVO
from modules.clients.slack_client import SlackManager
from modules.clients.tiktok_client import TikTokManager
from modules.clients.twitch_client import TwitchManager
from modules.clients.youtube_client import YouTubeManager

def handle_exit(sig, frame):
    print("\n👋 Kim se ha ido a dormir instantáneamente.")
    os._exit(0)

async def main():
    args = parse_arguments()
    
    try:
        loader = ConfigLoader()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return

    bot_identity = loader.get_env("BOT_NAME", "Kimera")
    streamer_identity = loader.get_env("STREAMER_NAME", "Klumsy")

    print(f"\n{'='*50}\n      🤖 SISTEMA OPERATIVO {bot_identity.upper()} V2.0\n{'='*50}\n")

    # 1. INICIALIZAR MEMORIA (7 días de persistencia)
    # Esto crea una carpeta /memory con archivos JSON
    memory = MemoryManager(memory_dir="memory", max_days=7)

    # 2. INICIALIZACIÓN DE MOTORES (Pasamos la memoria al procesador)
    processor = KimeraProcessor(loader, memory) # <--- Ahora el procesador tiene memoria
    tts = TTSEngine(loader)
    
    tasks = []
    tasks.append(asyncio.create_task(tts.worker()))

    # 3. ACTIVACIÓN DE PLATAFORMAS
    if args.all or getattr(args, 'slack', False):
        sm = SlackManager(loader, processor, tts)
        tasks.append(asyncio.create_task(sm.run()))

    if args.twitch or args.all:
        tm = TwitchManager(loader, processor, tts)
        tasks.append(asyncio.create_task(tm.start()))

    if args.youtube or args.all:
        ym = YouTubeManager(loader, processor, tts)
        tasks.append(asyncio.create_task(ym.start()))

    if args.tiktok or args.all:
        tkm = TikTokManager(loader, processor, tts)
        tasks.append(asyncio.create_task(tkm.run()))

    # Saludo inicial
    await tts.reproducir_y_esperar(f"Sistema iniciado. Hola {streamer_identity}")
    print(f"🚀 {bot_identity.upper()} ESCUCHANDO CON MEMORIA ACTIVA.\n")

    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        handle_exit(None, None)
    finally:
        for task in tasks: 
            task.cancel()
        os._exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        handle_exit(None, None)