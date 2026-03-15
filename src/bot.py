import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.config_loader import ConfigLoader
from modules.processor import KimeraProcessor
from modules.tts_engine import TTSEngine
from modules.cli_parser import parse_arguments 
from modules.twitch_client import TwitchManager
from modules.youtube_client import YouTubeManager
from modules.tiktok_client import TikTokManager

async def main():
    args = parse_arguments()
    try:
        loader = ConfigLoader()
    except Exception as e:
        print(f"❌ Error crítico: {e}"); return

    bot_identity = loader.get_env("BOT_NAME", "Kimera")
    streamer_identity = loader.get_env("STREAMER_NAME", "Klumsy")

    print(f"\n{'='*50}\n      🤖 SISTEMA OPERATIVO {bot_identity.upper()} V2.0\n{'='*50}\n")

    processor = KimeraProcessor(loader)
    tts = TTSEngine(loader)
    
    tasks = []
    tasks.append(asyncio.create_task(tts.worker()))

    if args.twitch or args.all:
        tm = TwitchManager(loader, processor, tts)
        tasks.append(asyncio.create_task(tm.start()))

    if args.tiktok or args.all:
        tkm = TikTokManager(loader, processor, tts)
        tasks.append(asyncio.create_task(tkm.run())) # Ahora sí coincide con TikTokManager.run

    await tts.agregar_a_cola(f"Sistema iniciado. Hola {streamer_identity}")
    print(f"🚀 {bot_identity.upper()} ESCUCHANDO.\n")

    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        print(f"\n🛑 Apagando...")
    finally:
        for task in tasks: task.cancel()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)