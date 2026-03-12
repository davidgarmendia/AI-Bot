import asyncio
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
# Añadimos la carpeta actual al PATH para que Python reconozca la carpeta 'modules'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
# Cada módulo tiene una responsabilidad única (Principio de Responsabilidad Única)
from modules.config_loader import ConfigLoader    # Cimiento: Carga de archivos y .env
from modules.processor import KimeraProcessor      # Cerebro: IA y Filtros de seguridad
from modules.tts_engine import TTSEngine           # Voz: Generación de audio y colas
from modules.twitch_client import TwitchManager    # Oído 1: Conector Twitch (Lectura Total)
from modules.youtube_client import YouTubeManager  # Oído 2: Conector YouTube (Lectura Total)
from modules.tiktok_client import TikTokManager    # Oído 3: Conector TikTok (Filtro Keyword)

async def main():
    print("\n" + "="*50)
    print("      🤖 SISTEMA OPERATIVO KIMERA V2.0")
    print("           (Arquitectura Modular)")
    print("="*50 + "\n")

    # 1. INICIALIZACIÓN DE CONFIGURACIÓN
    # Cargamos tokens y reglas antes de que cualquier otro módulo arranque.
    try:
        loader = ConfigLoader()
        print("✅ ConfigLoader: Archivos JSON y .env validados.")
    except Exception as e:
        print(f"❌ Error crítico al cargar configuración: {e}")
        return

    # 2. INICIALIZACIÓN DE MOTORES CORE
    # El Processor (IA) y el TTS (Voz) son compartidos por todas las plataformas.
    processor = KimeraProcessor(loader)
    tts = TTSEngine(loader)
    print("✅ Motores Core (IA y TTS) en línea.")

    # 3. INSTANCIACIÓN DE CONECTORES (SENTIDOS)
    # Creamos los clientes para cada plataforma inyectando los motores core.
    twitch_bot = TwitchManager(loader, processor, tts)
    youtube_bot = YouTubeManager(loader, processor, tts)
    tiktok_bot = TikTokManager(loader, processor, tts)

    # 4. ARRANQUE DE TAREAS ASÍNCRONAS (Paralelismo)
    # Usamos create_task para que todos los módulos corran al mismo tiempo sin bloquearse.
    print("\n📡 Iniciando conectores de plataforma...")
    
    # Motor de voz (Siempre activo para procesar la cola de audios)
    asyncio.create_task(tts.worker())
    
    # Clientes de chat
    asyncio.create_task(twitch_bot.start())
    asyncio.create_task(youtube_bot.start())
    asyncio.create_task(tiktok_bot.start())

    # 5. PRUEBA DE INTEGRACIÓN (Smoke Test)
    # Un saludo inicial confirma que el flujo Config -> IA -> TTS funciona.
    streamer_name = loader.get_env("TIKTOK_NICKNAME", "Creador")
    welcome_msg = f"¡Sistema Kimera iniciado! Hola {streamer_name}, estoy lista para el stream."
    
    print(f"🎙️ Kimera: Generando saludo inicial...")
    await tts.agregar_a_cola(welcome_msg)

    print("\n" + "-"*50)
    print("🚀 KIMERA ESTÁ ESCUCHANDO EN TWITCH, YOUTUBE Y TIKTOK")
    print("Presiona Ctrl+C para apagar el sistema.")
    print("-"*50 + "\n")

    # 6. MANTENIMIENTO DEL BUCLE PRINCIPAL
    # Mantenemos el bot vivo indefinidamente.
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("\n👋 Tareas canceladas por el sistema.")
    except KeyboardInterrupt:
        print("\n👋 Apagado manual detectado. Cerrando procesos de Kimera...")
    finally:
        # Aquí podrías añadir lógica de cierre de archivos o desconexión de APIs
        print("🔒 Sistema fuera de línea.")

if __name__ == "__main__":
    # Ajuste de política de bucle para evitar errores de cierre en Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        # Iniciamos la ejecución del orquestador
        asyncio.run(main())
    except KeyboardInterrupt:
        # Captura el Ctrl+C en la terminal para un cierre limpio
        pass