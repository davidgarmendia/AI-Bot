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

# 1. CARGAR CONFIGURACIÓN PRIVADA
load_dotenv()
NICKNAME = os.getenv("TIKTOK_NICKNAME")

# 2. CONFIGURACIÓN PÚBLICA
client_ai = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
VOICE = "es-MX-DaliaNeural" 

# Inicializar audio
pygame.mixer.init()

# Carpeta de audios
AUDIO_DIR = "audios"
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# 3. FUNCIÓN DE VOZ CON EPOCH Y LIMPIEZA
async def hablar(texto):
    # Generamos un nombre único usando Epoch
    epoch_time = int(time.time())
    filename = os.path.join(AUDIO_DIR, f"kim_{epoch_time}.mp3")
    
    try:
        # Generar el audio (Proceso bloqueante hasta que el archivo esté escrito)
        communicate = edge_tts.Communicate(texto, VOICE)
        await communicate.save(filename)
        
        # QA Check: Esperar a que el Sistema Operativo libere el archivo
        await asyncio.sleep(0.2)

        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            # Cargar y reproducir
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Soltar y borrar para mantener limpio el disco
            pygame.mixer.music.unload()
            os.remove(filename)
        else:
            print(f"⚠️ No se pudo generar el audio: {filename}")

    except Exception as e:
        print(f"❌ Error en el flujo de audio: {e}")

# 4. LÓGICA DE FILTRADO Y RESPUESTA
client_tiktok = TikTokLiveClient(unique_id=NICKNAME)

@client_tiktok.on(CommentEvent)
async def on_comment(event: CommentEvent):
    # Convertimos a minúsculas para una comparación justa
    mensaje_usuario = event.comment.lower()
    
    # REGLA DE ORO: Solo responder si mencionan 'kim' o 'kimera' como palabras completas
    # El uso de \b evita que responda a 'kimono', 'kimchi' o 'joaquim'
    if not re.search(r"\b(kim|kimera)\b", mensaje_usuario):
        return

    # Si pasa el filtro, procesamos la respuesta
    print(f"✨ Mención detectada de {event.user.nickname}: {event.comment}")

    try:
        completion = client_ai.chat.completions.create(
            model="meta-llama-3-8b-instruct",
            messages=[
                {"role": "system", "content": (
                    f"Tu nombre es Kimera (o Kim). Eres la sanadora torpe del stream de {NICKNAME}. "
                    "Solo respondes cuando te hablan directamente. "
                    "Eres divertida, usas términos de gachas y a veces te equivocas con tus pociones. "
                    "Mantén tus respuestas muy breves (máximo 2 frases)."
                )},
                {"role": "user", "content": f"El usuario {event.user.nickname} dice: {event.comment}"}
            ]
        )
        
        respuesta = completion.choices[0].message.content
        print(f"🤖 Kim: {respuesta}")
        
        # Ejecutar voz sin bloquear el chat
        asyncio.create_task(hablar(respuesta))

    except Exception as e:
        print(f"❌ Error de IA: {e}")

# 5. LANZAMIENTO
if __name__ == "__main__":
    os.environ['WITH_PING'] = 'true'
    
    print(f"🚀 AI-Bot Conectado: {NICKNAME}")
    print(f"🛡️ Modo Escucha Activo: Kim solo responderá a menciones directas.")
    
    try:
        client_tiktok.run()
    except KeyboardInterrupt:
        print("\n👋 Desconectando a Kimera...")