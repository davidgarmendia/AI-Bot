import asyncio
import sys
import os
import signal
import traceback

# 1. FORZAR RUTA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, ".."))

from modules.config_loader import ConfigLoader
from modules.processor import KimeraProcessor
from modules.tts_engine import TTSEngine
from modules.cli_parser import parse_arguments 
from modules.memory_manager import MemoryManager
from modules.clients.twitch_client import TwitchManager

def handle_exit(sig, frame):
    print("\n👋 Kim se ha ido a dormir.")
    os._exit(0)

async def main():
    try:
        args = parse_arguments()
        loader = ConfigLoader()

        bot_name = loader.get_env("BOT_NAME", "Kimera")
        streamer_name = loader.get_env("STREAMER_NAME", "Klumsy")

        print(f"\n{'='*50}")
        print(f"      🤖 SISTEMA OPERATIVO {bot_name.upper()} V2.0")
        print(f"{'='*50}\n")

        # Motores
        memory = MemoryManager(memory_dir="memory", max_days=7)
        processor = KimeraProcessor(loader, memory)
        tts = TTSEngine(loader)
        
        tasks = []
        # Comentado para evitar bloqueos con AllTalk apagado
        tasks.append(asyncio.create_task(tts.worker()))

        if args.twitch or args.all:
            tm = TwitchManager(loader, processor, tts)
            # Iniciamos Twitch
            tasks.append(asyncio.create_task(tm.start()))
            print("✅ Twitch: Cargado y listo.")

        # --- CAMBIO CRÍTICO: COMENTAR ESTA LÍNEA ---
        # print("Iniciando saludo...")
        # await tts.reproducir_y_esperar(f"Sistema iniciado. Hola {streamer_name}")
        
        print(f"🚀 {bot_name.upper()} ESCUCHANDO...\n")

        # Esto ejecuta las tareas (Twitch) y las mantiene vivas
        if tasks:
            await asyncio.gather(*tasks)
        else:
            print("⚠️ No hay tareas activas. Usa --twitch")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO AL ARRANCAR:\n{e}")
        traceback.print_exc()
        input("\nPresiona ENTER para cerrar...")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    
    # Ajuste para Python 3.14 en Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Usar un loop explícito suele ser más estable en versiones experimentales de Python
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        handle_exit(None, None)
    except Exception as e:
        print(f"Error fatal: {e}")
        input("Presiona ENTER...")
    finally:
        loop.close()