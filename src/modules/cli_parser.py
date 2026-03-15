import argparse

def parse_arguments():
    """
    QA Logic: Separa la captura de comandos de la ejecución del bot.
    """
    parser = argparse.ArgumentParser(description="Selector de plataformas Kimera V2.0")
    
    # Flags de plataformas
    parser.add_argument("--twitch", action="store_true", help="Activar Twitch")
    parser.add_argument("--youtube", action="store_true", help="Activar YouTube")
    parser.add_argument("--tiktok", action="store_true", help="Activar TikTok")
    parser.add_argument("--all", action="store_true", help="Activar todas las plataformas")
    parser.add_argument("--slack", action="store_true", help="Ejecutar el bot en Slack")
    # Flag de modo debug (opcional para el futuro)
    parser.add_argument("--debug", action="store_true", help="Modo desarrollador")

    return parser.parse_args()