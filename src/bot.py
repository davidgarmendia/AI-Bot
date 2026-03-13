import asyncio
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
# Esto permite que Python encuentre la carpeta 'modules' correctamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
from modules.config_loader import ConfigLoader
from modules.processor import KimeraProcessor
from modules.tts_engine import TTSEngine
from modules.cli_parser import parse_arguments  # Nuestro nuevo gestor de comandos
from modules.twitch_client import TwitchManager
from modules.youtube_client import YouTubeManager
from modules.tiktok_client import TikTokManager

async def main():
    # 0. CAPTURA DE ARGUMENTOS
    # Detecta qué escribiste en la terminal (--tiktok, --youtube, etc.)
    args = parse_arguments()

    # 1. INICIALIZACIÓN DE CONFIGURACIÓN
    try:
        loader = ConfigLoader()
        print("✅ ConfigLoader: Recursos de configuración cargados.")
    except Exception as e:
        print(f"❌ Error crítico al cargar configuración: {e}")
        return

    # Nombres protegidos desde el .env
    bot_identity = loader.get_env("BOT_NAME", "Kimera")
    streamer_identity = loader.get_env("STREAMER_NAME", "Klumsy")

    print("\n" + "="*50)
    print(f"      🤖 SISTEMA OPERATIVO {bot_identity.upper()} V2.0")
    print("           (Arquitectura Modular)")
    print("="*50 + "\n")

    # 2. INICIALIZACIÓN DE MOTORES CORE
    # La IA y la Voz se cargan siempre porque son el corazón del bot
    processor = KimeraProcessor(loader)
    tts = TTSEngine(loader)
    print("✅ Motores Core (IA y TTS) en línea.")

    # 3. INSTANCIACIÓN Y ARRANQUE DINÁMICO
    print(f"📡 {bot_identity} iniciando conectores seleccionados...")
    
    # El motor de voz siempre arranca para procesar la cola
    asyncio.create_task(tts.worker())

    active_platforms = []

    # Lógica de encendido selectivo basada en los comandos de la terminal
    if args.twitch or args.all:
        try:
            twitch_bot = TwitchManager(loader, processor, tts)
            asyncio.create_task(twitch_bot.start())
            active_platforms.append("TWITCH")
        except Exception as e:
            print(f"⚠️ Error al conectar con Twitch: {e}")

    if args.youtube or args.all:
        try:
            youtube_bot = YouTubeManager(loader, processor, tts)
            asyncio.create_task(youtube_bot.start())
            active_platforms.append("YOUTUBE")
        except Exception as e:
            print(f"⚠️ Error al conectar con YouTube: {e}")

    if args.tiktok or args.all:
        try:
            tiktok_bot = TikTokManager(loader, processor, tts)
            asyncio.create_task(tiktok_bot.start())
            active_platforms.append("TIKTOK")
        except Exception as e:
            print(f"⚠️ Error al conectar con TikTok: {e}")

    # 4. SALUDO INICIAL (Smoke Test)
    welcome_msg = f"¡Sistema iniciado! Hola {streamer_identity}, estoy lista para el stream."
    print(f"🎙️ {bot_identity}: Generando saludo inicial...")
    await tts.agregar_a_cola(welcome_msg)

    print("\n" + "-"*50)
    plataformas_str = ", ".join(active_platforms) if active_platforms else "MODO PRUEBA (Sin chats)"
    print(f"🚀 {bot_identity.upper()} ESCUCHANDO EN: {plataformas_str}")
    print(f"👤 Identidad activa: {streamer_identity}")
    print("Presiona Ctrl+C para apagar el sistema.")
    print("-"*50 + "\n")

    # 5. MANTENIMIENTO DEL BUCLE PRINCIPAL
    try:
        while True:
            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\n👋 Apagado detectado. Cerrando procesos de Kimera...")
    finally:
        print("🔒 Sistema fuera de línea.")

if __name__ == "__main__":
    # Ajustes para Windows y limpieza de consola
    if sys.platform == 'win32':
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass