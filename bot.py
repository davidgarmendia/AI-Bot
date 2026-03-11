import asyncio
import edge_tts
import pygame
import os
import re
import time
from dotenv import load_dotenv
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
from openai import OpenAI

# 1. CARGAR CONFIGURACIÓN PRIVADA (.env)
load_dotenv()
NICKNAME = os.getenv("TIKTOK_NICKNAME")
# Estas variables ocultan el nombre real en GitHub
KEYWORD1 = os.getenv("BOT_NAME_PRIMARY", "Bot").lower()
KEYWORD2 = os.getenv("BOT_NAME_SECONDARY", "Asistente").lower()

# 2. CONFIGURACIÓN DE IA Y AUDIO
client_ai = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
VOICE = "es-MX-DaliaNeural" 

# Inicializar mezclador de audio
pygame.mixer.init()

# Asegurar que la carpeta de audios existe
AUDIO_DIR = "audios"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# 3. FUNCIÓN DE VOZ (Sincronizada con Epoch)
async def hablar(texto):
    epoch_time = int(time.time())
    filename = os.path.join(AUDIO_DIR, f"voice_{epoch_time}.mp3")
    
    try:
        # Generar audio con Edge-TTS
        communicate = edge_tts.Communicate(texto, VOICE)
        await communicate.save(filename)
        
        # Pequeño margen para que el SO cierre el archivo
        await asyncio.sleep(0.2)

        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Reproducción con Pygame
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Limpieza: Soltar archivo y eliminarlo del disco
            pygame.mixer.music.unload()
            os.remove(filename)
        else:
            print(f"⚠️ Error: El archivo {filename} está vacío o no existe.")

    except Exception as e:
        print(f"❌ Error en el sistema de audio: {e}")

# 4. LÓGICA DE FILTRADO Y RESPUESTA (Incógnito)
client_tiktok = TikTokLiveClient(unique_id=NICKNAME)

@client_tiktok.on(CommentEvent)
async def on_comment(event: CommentEvent):
    mensaje_usuario = event.comment.lower()
    
    # FILTRO: Solo responde si mencionan las palabras clave del .env
    patron_secreto = rf"\b({KEYWORD1}|{KEYWORD2})\b"
    
    if not re.search(patron_secreto, mensaje_usuario):
        return

    print(f"✨ Mención detectada de {event.user.nickname}")

    try:
        # Configuración del Prompt usando las variables del .env
        completion = client_ai.chat.completions.create(
            model="meta-llama-3-8b-instruct",
            messages=[
                {"role": "system", "content": (
                    f"Tu nombre es {KEYWORD1.capitalize()}. Eres una sanadora torpe "
                    f"en el stream de {NICKNAME}. Responde de forma muy breve, "
                    "divertida y usando términos de juegos gacha."
                )},
                {"role": "user", "content": f"El usuario {event.user.nickname} dice: {event.comment}"}
            ]
        )
        
        respuesta = completion.choices[0].message.content
        print(f"🤖 {KEYWORD1.capitalize()}: {respuesta}")
        
        # Crear tarea asíncrona para no bloquear el chat mientras habla
        asyncio.create_task(hablar(respuesta))

    except Exception as e:
        print(f"❌ Error en la respuesta de IA: {e}")

# 5. EJECUCIÓN DEL BOT
if __name__ == "__main__":
    # Estabilidad para conexiones TikTok
    os.environ['WITH_PING'] = 'true'
    
    print(f"🚀 AI-Bot activo para el usuario: {NICKNAME}")
    print(f"🛡️  Filtro dinámico activado. Esperando menciones...")
    
    try:
        client_tiktok.run()
    except KeyboardInterrupt:
        print("\n👋 Cerrando el sistema de {KEYWORD1.capitalize()}...")