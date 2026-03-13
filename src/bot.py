import asyncio
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
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

    # 1. INICIALIZACIÓN
    try:
        loader = ConfigLoader()
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return

    bot_identity = loader.get_env("BOT_NAME", "Kimera")
    streamer_identity = loader.get_env("STREAMER_NAME", "Klumsy")

    print("\n" + "="*50)
    print(f"      🤖 SISTEMA OPERATIVO {bot_identity.upper()} V2.0")
    print("="*50 + "\n")

    # 2. MOTORES CORE
    processor = KimeraProcessor(loader)
    tts = TTSEngine(loader)
    
    # Lista para rastrear todos los managers y poder detenerlos
    managers = []
    
    # 3. LANZAMIENTO DE TAREAS
    # Guardamos las tareas para poder cancelarlas al final
    tasks = []
    tasks.append(asyncio.create_task(tts.worker()))

    if args.twitch or args.all:
        tm = TwitchManager(loader, processor, tts)
        managers.append(tm)
        tasks.append(asyncio.create_task(tm.start()))

    if args.youtube or args.all:
        ym = YouTubeManager(loader, processor, tts)
        managers.append(ym)
        tasks.append(asyncio.create_task(ym.start()))

    if args.tiktok or args.all:
        tkm = TikTokManager(loader, processor, tts)
        managers.append(tkm)
        tasks.append(asyncio.create_task(tkm.start()))

    # Saludo inicial
    plantilla_saludo = loader.get_dialogue("saludos", "inicio_sistema")
    welcome_msg = plantilla_saludo.replace("{streamer}", streamer_identity)
    await tts.agregar_a_cola(welcome_msg)

    print(f"🚀 {bot_identity.upper()} ESCUCHANDO. Ctrl+C para salir.\n")

    # 4. MANEJO DEL CIERRE (GRACEFUL SHUTDOWN)
    try:
        # En lugar de while True, esperamos a que las tareas terminen 
        # o que ocurra una interrupción
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        print(f"\n\n🛑 Detectado apagado. Deteniendo conectores de {bot_identity}...")
    finally:
        # ORDEN DE CIERRE:
        # 1. Decirle a los managers que dejen de procesar bucles
        for manager in managers:
            if hasattr(manager, 'stop'):
                manager.stop()
        
        # 2. Cancelar todas las tareas de asyncio activas
        for task in tasks:
            task.cancel()
        
        # Esperar un segundo para que las tareas limpien
        await asyncio.gather(*tasks, return_exceptions=True)
        print("🔒 Todos los procesos terminados. Sistema fuera de línea.")

if __name__ == "__main__":
    # Configuración específica para Windows y señales de interrupción
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Captura el Ctrl+C al nivel más alto para evitar el molesto Traceback de Python
        sys.exit(0)