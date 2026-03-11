import asyncio
# import pygame
import playsound
import os
import re
import time
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
from twitchio.ext import commands
from openai import OpenAI
import edge_tts
from playsound import playsound

# --- CONFIGURACIÓN DE RUTAS ---
# Detecta la raíz del proyecto para encontrar .env y config.json
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
    SYSTEM_PROMPT_TEMPLATE = "Responde brevemente y sin emojis."

# --- VARIABLES DE ENTORNO ---
T_NICK = os.getenv("TIKTOK_NICKNAME")
TW_TOKEN = os.getenv("TWITCH_TOKEN")
TW_CHANNEL = os.getenv("TWITCH_CHANNEL")
KEYWORD1 = os.getenv("BOT_NAME_PRIMARY", "Bot").lower()
KEYWORD2 = os.getenv("BOT_NAME_SECONDARY", "Asistente").lower()
AUDIO_DIR = os.path.join(BASE_DIR, "audios")

# --- MOTORES Y COLAS ---
client_ai = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
audio_queue = asyncio.Queue(maxsize=10)

# --- LÓGICA DE AUDIO (Utilizando playsound) ---
def limpiar_audios():
    if os.path.exists(AUDIO_DIR):
        shutil.rmtree(AUDIO_DIR)
    os.makedirs(AUDIO_DIR)
    print(f"🧹 Carpeta de audios lista en: {AUDIO_DIR}")

async def worker_audio():
    print("🛠️ Trabajador de audio iniciado...")
    while True:
        texto = await audio_queue.get()
        
        # Generar nombre de archivo único
        filename = os.path.join(AUDIO_DIR, f"v_{int(time.time())}.mp3")
        try:
            # Generar el habla con Edge-TTS
            communicate = edge_tts.Communicate(texto, "es-MX-DaliaNeural")
            await communicate.save(filename)
            
            # playsound bloquea el hilo hasta que termina de sonar (perfecto para la cola)
            # Se usa una tarea de hilo para no bloquear el loop de asyncio
            await asyncio.to_thread(playsound, filename)
            
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"🔊 Error en reproducción de audio: {e}")
        
        audio_queue.task_done()

# --- PROCESAMIENTO DE IA (Modular para ambas plataformas) ---
async def procesar_ia(usuario, mensaje):
    if audio_queue.full():
        print(f"⏳ Cola llena. Ignorando a {usuario}.")
        return

    start_time = time.time()
    try:
        # Inyectar nombre del bot en las reglas
        prompt = SYSTEM_PROMPT_TEMPLATE.format(name=KEYWORD1.capitalize())
        
        completion = client_ai.chat.completions.create(
            model="meta-llama-3-8b-instruct",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": mensaje}
            ]
        )
        
        # Captura respuesta y limpia emojis (ASCII filter)
        respuesta = completion.choices[0].message.content
        respuesta_limpia = re.sub(r'[^\x00-\x7F]+', '', respuesta)
        
        latencia = time.time() - start_time
        print(f"⏱️ [{usuario}] IA tardó: {latencia:.2f}s | Respuesta: {respuesta_limpia}")
        
        await audio_queue.put(respuesta_limpia)
    except Exception as e:
        print(f"❌ Error procesando IA: {e}")

# --- CLIENTE TWITCH (TwitchIO) ---
class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(token=TW_TOKEN, prefix='!', initial_channels=[TW_CHANNEL])

    async def event_message(self, msg):
        # Ignorar mensajes del propio bot
        if msg.author and msg.author.name.lower() == TW_CHANNEL.lower():
            return
        
        # Detectar mención
        if re.search(rf"\b({KEYWORD1}|{KEYWORD2})\b", msg.content.lower()):
            await procesar_ia(msg.author.name, msg.content)

# --- CLIENTE TIKTOK (TikTokLive) ---
tt_client = TikTokLiveClient(unique_id=T_NICK)

@tt_client.on(CommentEvent)
async def on_tt_comment(event: CommentEvent):
    # Detectar mención
    if re.search(rf"\b({KEYWORD1}|{KEYWORD2})\b", event.comment.lower()):
        await procesar_ia(event.user.nickname, event.comment)

# --- PUNTO DE ENTRADA PRINCIPAL ---
async def main():
    limpiar_audios()
    
    # Iniciar bot de Twitch
    tw_bot = TwitchBot()
    
    # Iniciar tareas en paralelo
    loop = asyncio.get_event_loop()
    loop.create_task(worker_audio())
    loop.create_task(tw_bot.connect())
    
    print(f"🚀 Multistream Activo!")
    print(f"📺 TikTok: @{T_NICK} | 💜 Twitch: #{TW_CHANNEL}")
    
    try:
        await tt_client.start()
    except Exception as e:
        print(f"❌ Error en cliente TikTok: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Sistema apagado por el usuario. ¡Suerte en el stream!")