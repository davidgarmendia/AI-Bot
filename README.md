# AI TTS Chat Bot Companion - V 1.0

## Descripcion
Sistema avanzado de asistencia para streaming multiplataforma. Kimera utiliza Inteligencia Artificial (LLM) para interactuar con audiencias de Twitch, YouTube y TikTok de forma simultanea. El sistema integra procesamiento de lenguaje natural, sintesis de voz asincrona y deteccion automatica de transmisiones en vivo.

## Estructura del Proyecto
El codigo se organiza bajo una arquitectura modular para facilitar el mantenimiento y la escalabilidad:

* **src/bot.py**: Orquestador principal que gestiona el ciclo de vida de todos los modulos.
* **src/modules/config_loader.py**: Centraliza la carga de variables de entorno (.env) y configuraciones JSON.
* **src/modules/processor.py**: Gestiona la comunicacion con el motor de IA (LM Studio) y aplica filtros de seguridad.
* **src/modules/tts_engine.py**: Motor de voz basado en Edge-TTS con gestion de colas para evitar solapamiento de audio.
* **src/modules/twitch_client.py**: Cliente IRC para integracion con el chat de Twitch.
* **src/modules/youtube_client.py**: Conector dinamico que localiza automaticamente el directo activo del canal.
* **src/modules/tiktok_client.py**: Cliente de escucha para TikTok con logica de activacion por palabras clave (Triggers).

## Requisitos de Entorno
* Python 3.10+
* LM Studio (Local LLM Server)
* FFmpeg (Requerido para el procesamiento de audio en algunos sistemas)

## Instalacion
1. Clonar el repositorio.
2. Crear un entorno virtual: `python -m venv venv`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar el archivo `.env` con las credenciales necesarias.

## Ejecucion
Para iniciar todos los servicios simultaneamente, ejecute:
python src/bot.py

## Notas de QA
El sistema implementa una arquitectura asincrona mediante asyncio, permitiendo que cada plataforma opere de forma independiente sin bloquear el flujo principal de procesamiento de IA o la salida de voz.