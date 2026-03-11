import asyncio
import edge_tts
import pygame
import os
import re
import time
import shutil # Para limpieza de carpetas
from dotenv import load_dotenv
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
from openai import OpenAI

# 1. CONFIGURACIÓN Y LIMPIEZA INICIAL
load_dotenv()
NICKNAME = os.getenv("TIKTOK_NICKNAME")
KEYWORD1 = os.getenv("BOT_NAME_PRIMARY", "Bot").lower()
KEYWORD2 = os.getenv("BOT_NAME_SECONDARY", "Asistente").lower()

AUDIO_DIR = "audios"

def limpiar_carpeta_audios():
    """QA: Elimina archivos residuales de sesiones anteriores al iniciar."""
    if os.path.exists(AUDIO_DIR):
        shutil.rmtree(AUDIO_DIR)
    os.makedirs(AUDIO_DIR)
    print(f"🧹 Carpeta {AUDIO_DIR} purificada.")

limpiar_carpeta_audios()

client_ai = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
VOICE = "es-MX-DaliaNeural"
pygame.mixer.init()

# 2. COLA CON LÍMITE (Maxsize)
# Si la cola llega a 10, el bot dejará de aceptar peticiones hasta procesar las actuales.
audio_queue = asyncio.Queue(maxsize=10)

async def worker_de_audio():
    while True:
        texto_para_hablar = await audio_queue.get()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.2)
            
        await ejecutar_voz(texto_para_hablar)
        audio_queue.task_done()

async def ejecutar_voz(texto):
    epoch_time = int(time.time())
    filename = os.path.join(AUDIO_DIR, f"voice_{epoch_time}.mp3")
    
    try:
        communicate = edge_tts.Communicate(texto, VOICE)
        await communicate.save(filename)
        await asyncio.sleep(0.2)

        if os.path.exists(filename):
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            pygame.mixer.music.unload()
            os.remove(filename) # Borrado inmediato tras uso
    except Exception as e:
        print(f"⚠️ Error de audio: {e}")

# 3. LÓGICA DE TIKTOK CON CONTROL DE FLUJO
client_tiktok = TikTokLiveClient(unique_id=NICKNAME)

@client_tiktok.on(CommentEvent)
async def on_comment(event: CommentEvent):
    mensaje_usuario = event.comment.lower()
    patron = rf"\b({KEYWORD1}|{KEYWORD2})\b"
    
    if not re.search(patron, mensaje_usuario):
        return

    # QA: Verificar si la cola está llena antes de procesar con IA (Ahorra recursos)
    if audio_queue.full():
        print(f"⏳ Cola llena. Ignorando mención de {event.user.nickname} para evitar saturación.")
        return

    print(f"✨ Procesando mención de {event.user.nickname}...")

    try:
        completion = client_ai.chat.completions.create(
            model="meta-llama-3-8b-instruct",
            messages=[
                {"role": "system", "content": f"Tu nombre es {KEYWORD1}. Responde muy breve."},
                {"role": "user", "content": event.comment}
            ]
        )
        
        respuesta = completion.choices[0].message.content
        await audio_queue.put(respuesta)

    except Exception as e:
        print(f"❌ Error en IA: {e}")

async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(worker_de_audio())
    print(f"🚀 Sistema activo para: {NICKNAME}")
    await client_tiktok.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Cerrando sistema...")