import asyncio
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
from modules.config_loader import ConfigLoader
from modules.processor import KimeraProcessor
from modules.tts_engine import TTSEngine
from modules.twitch_client import TwitchManager
from modules.youtube_client import YouTubeManager
from modules.tiktok_client import TikTokManager

async def main():
    # 1. INICIALIZACIÓN DE CONFIGURACIÓN
    try:
        loader = ConfigLoader()
        print("✅ ConfigLoader: Recursos cargados.")
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return

    # Extraemos nombres protegidos desde el loader (.env)
    # Si no existen, usamos valores genéricos por seguridad
    bot_identity = loader.get_env("BOT_NAME", "La Entidad")
    streamer_identity = loader.get_env("STREAMER_NAME", "Streamer")

    print("\n" + "="*50)
    print(f"      🤖 SISTEMA OPERATIVO {bot_identity.upper()} V2.0")
    print("           (Identidad Protegida)")
    print("="*50 + "\n")

    # 2. INICIALIZACIÓN DE MOTORES CORE
    processor = KimeraProcessor(loader)
    tts = TTSEngine(loader)
    print("✅ Motores Core en línea.")

    # 3. INSTANCIACIÓN DE CONECTORES
    # Twitch desactivado por hoy para evitar el error de tokens
    youtube_bot = YouTubeManager(loader, processor, tts)
    tiktok_bot = TikTokManager(loader, processor, tts)

    # 4. ARRANQUE DE TAREAS
    print(f"📡 {bot_identity} iniciando conexión con plataformas...")
    asyncio.create_task(tts.worker())
    asyncio.create_task(youtube_bot.start())
    asyncio.create_task(tiktok_bot.start())

    # 5. PRUEBA DE INTEGRACIÓN (Con nombres anónimos)
    welcome_msg = f"¡Sistema iniciado! Hola {streamer_identity}, estoy lista para el stream."
    
    print(f"🎙️ {bot_identity}: Generando saludo inicial...")
    await tts.agregar_a_cola(welcome_msg)

    print("\n" + "-"*50)
    print(f"🚀 {bot_identity.upper()} ESCUCHANDO EN YOUTUBE Y TIKTOK")
    print(f"👤 Identidad activa: {streamer_identity}")
    print("Presiona Ctrl+C para apagar el sistema.")
    print("-"*50 + "\n")

    try:
        while True:
            await asyncio.sleep(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("\n🔒 Sistema fuera de línea.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass