import asyncio
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
import edge_tts
from playsound import playsound

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- CARGA DE REGLAS ---
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = json.load(f)
        SYSTEM_PROMPT_TEMPLATE = " ".join(config_data["system_rules"])
except:
    SYSTEM_PROMPT_TEMPLATE = "Responde brevemente y sin emojis."

# --- VARIABLES DE ENTORNO ---
T_NICK = os.getenv("TIKTOK_NICKNAME")
TW_TOKEN = os.getenv("TWITCH_TOKEN")
TW_CHANNEL = os.getenv("TWITCH_CHANNEL", "").lower()
TW_NICK = os.getenv("BOT_NAME_PRIMARY", "Kim").lower()
KEYWORD1 = TW_NICK
KEYWORD2 = os.getenv("BOT_NAME_SECONDARY", "Kimera").lower()
AUDIO_DIR = os.path.join(BASE_DIR, "audios")

# --- MOTORES ---
client_ai = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
audio_queue = asyncio.Queue(maxsize=10)

def limpiar_audios():
    if os.path.exists(AUDIO_DIR):
        shutil.rmtree(AUDIO_DIR)
    os.makedirs(AUDIO_DIR)

async def worker_audio():
    print("🛠️  Sistema de audio Kimera activo...")
    while True:
        texto = await audio_queue.get()
        filename = os.path.join(AUDIO_DIR, f"v_{int(time.time())}.mp3")
        try:
            # LINEA 52: ASEGÚRATE QUE ESTÉ COMPLETA
            communicate = edge_tts.Communicate(texto, "es-MX-DaliaNeural")
            await communicate.save(filename)
            await asyncio.to_thread(playsound, filename)
            if os.path.exists(filename): os.remove(filename)
        except Exception as e:
            print(f"🔊 Error Audio: {e}")
        audio_queue.task_done()

async def procesar_ia(usuario, mensaje):
    if audio_queue.full(): return
    
    # LISTA NEGRA DE PALABRAS
    blacklist = ["muerte", "morir", "asesinato", "matar", "asesinar", "muerto"]
    
    try:
        prompt = SYSTEM_PROMPT_TEMPLATE.format(name=KEYWORD1.capitalize())
        res = client_ai.chat.completions.create(
            model="meta-llama-3-8b-instruct",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": mensaje}],
            timeout=10
        )
        
        respuesta = res.choices[0].message.content
        
        # 1. FILTRO DE PALABRAS (Censura con ***)
        for palabra in blacklist:
            regex = re.compile(re.escape(palabra), re.IGNORECASE)
            respuesta = regex.sub("****", respuesta)

        # 2. FILTRO DE CARACTERES (Permite acentos y Ñ, quita emojis)
        # Este nuevo regex permite letras (a-z, A-Z), números, puntuación básica 
        # y caracteres especiales del español (áéíóúüñÁÉÍÓÚÜÑ)
        respuesta_limpia = re.sub(r'[^a-zA-Z0-9\s.,!?¡¿áéíóúüñÁÉÍÓÚÜÑ:;()-]', '', respuesta)
        
        print(f"✨ Kim dice: {respuesta_limpia}")
        await audio_queue.put(respuesta_limpia)
        
    except Exception as e:
        print(f"❌ Error IA: {e}")

async def conectar_twitch_irc():
    server = 'irc.chat.twitch.tv'
    port = 6667
    while True:
        try:
            reader, writer = await asyncio.open_connection(server, port)
            writer.write(f"PASS {TW_TOKEN}\r\n".encode())
            writer.write(f"NICK {TW_NICK}\r\n".encode())
            writer.write(f"JOIN #{TW_CHANNEL}\r\n".encode())
            await writer.drain()
            print(f"💜 Twitch: Conectado a #{TW_CHANNEL}")
            while True:
                line = await reader.readline()
                if not line: break
                msg = line.decode().strip()
                if msg.startswith("PING"):
                    writer.write("PONG :tmi.twitch.tv\r\n".encode())
                    await writer.drain()
                    continue
                if "PRIVMSG" in msg:
                    partes = msg.split(":", 2)
                    if len(partes) < 3: continue
                    usuario = partes[1].split("!")[0]
                    if usuario.lower() == TW_NICK.lower(): continue
                    contenido = partes[2]
                    if re.search(rf"\b({KEYWORD1}|{KEYWORD2})\b", contenido.lower()):
                        await procesar_ia(usuario, contenido)
        except Exception as e:
            print(f"⚠️ Error Twitch, reintentando...")
            await asyncio.sleep(5)

tt_client = TikTokLiveClient(unique_id=T_NICK)
@tt_client.on(CommentEvent)
async def on_tt_comment(event: CommentEvent):
    if re.search(rf"\b({KEYWORD1}|{KEYWORD2})\b", event.comment.lower()):
        await procesar_ia(event.user.nickname, event.comment)

async def mantener_tiktok():
    while True:
        try:
            await tt_client.start()
        except:
            await asyncio.sleep(20)

async def main():
    limpiar_audios()
    stop_event = asyncio.Event()
    asyncio.create_task(worker_audio())
    asyncio.create_task(conectar_twitch_irc())
    asyncio.create_task(mantener_tiktok())
    print(f"🚀 SISTEMA ONLINE (Kim/Kimera)")
    await stop_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot apagado.")