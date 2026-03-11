import asyncio
import edge_tts
import pygame
import os
import re
import time
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
from openai import OpenAI

# --- CONFIGURACIÓN DE RUTAS ---
# Determinamos la raíz del proyecto (un nivel arriba de /src)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- CARGA DE REGLAS EXTERNAS ---
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        SYSTEM_PROMPT_TEMPLATE = " ".join(config_data["system_rules"])
except Exception as e:
    print(f"⚠️ Error cargando config.json: {e}")
    SYSTEM_PROMPT_TEMPLATE = "Responde de forma breve y sin emojis."

# --- VARIABLES DE ENTORNO ---
NICKNAME = os.getenv("TIKTOK_NICKNAME")
KEYWORD1 = os.getenv("BOT_NAME_PRIMARY", "Bot").lower()
KEYWORD2 = os.getenv("BOT_NAME_SECONDARY", "Asistente").lower()
AUDIO_DIR = os.path.join(BASE_DIR, "audios")

def limpiar_carpeta_audios():
    if os.path.exists(AUDIO_DIR):
        shutil.rmtree(AUDIO_DIR)
    os.makedirs(AUDIO_DIR)
    print(f"🧹 Carpeta de audios purificada en: {AUDIO_DIR}")

limpiar_carpeta_audios()

# --- INICIALIZACIÓN DE MOTORES ---
client_ai = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
VOICE = "es-MX-DaliaNeural"
pygame.mixer.init()

# Cola con límite de 10 mensajes para evitar desborde
audio_queue = asyncio.Queue(maxsize=10)

async def worker_de_audio():
    print("🛠️ Procesador de cola de audio iniciado...")
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
            os.remove(filename)
    except Exception as e:
        print(f"⚠️ Error en reproducción: {e}")

# --- LÓGICA DE TIKTOK ---
client_tiktok = TikTokLiveClient(unique_id=NICKNAME)

@client_tiktok.on(CommentEvent)
async def on_comment(event: CommentEvent):
    mensaje_usuario = event.comment.lower()
    patron = rf"\b({KEYWORD1}|{KEYWORD2})\b"
    
    if not re.search(patron, mensaje_usuario):
        return

    if audio_queue.full():
        print(f"⏳ Cola llena. Ignorando mención de {event.user.nickname}.")
        return

    try:
        # Insertamos el nombre del bot en la plantilla de reglas
        prompt_final = SYSTEM_PROMPT_TEMPLATE.format(name=KEYWORD1.capitalize())
        
        completion = client_ai.chat.completions.create(
            model="meta-llama-3-8b-instruct",
            messages=[
                {"role": "system", "content": prompt_final},
                {"role": "user", "content": event.comment}
            ]
        )
        
        respuesta = completion.choices[0].message.content
        
        # Filtro de seguridad: Eliminar cualquier carácter no-ASCII (emojis)
        respuesta_limpia = re.sub(r'[^\x00-\x7F]+', '', respuesta)
        
        print(f"🤖 Respuesta de {KEYWORD1.capitalize()}: {respuesta_limpia}")
        await audio_queue.put(respuesta_limpia)

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