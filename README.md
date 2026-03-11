# AI-Bot: Stream Interaction System

Asistente de interacción para transmisiones en vivo. Este sistema integra procesamiento de lenguaje natural mediante modelos de lenguaje de gran escala (LLM) y síntesis de voz (TTS) para generar respuestas automáticas y audibles en tiempo real.

## Arquitectura del Sistema

El bot opera bajo una arquitectura asíncrona que conecta cuatro componentes principales:
1. **Live Stream API:** Captura de eventos de chat en tiempo real.
2. **Inference Server (OpenAI API Wrapper):** Procesamiento de texto para la generación de respuestas dinámicas.
3. **TTS Engine:** Generación de audio de alta fidelidad.
4. **Audio Manager:** Gestión de la salida de audio local y control de archivos temporales.

## Características Técnicas

* **Filtrado Dinámico:** El sistema utiliza expresiones regulares para detectar menciones específicas definidas por el usuario, ignorando el tráfico de chat irrelevante.
* **Gestión de Archivos por Epoch:** Cada archivo de audio generado recibe un nombre único basado en el timestamp de Unix para prevenir colisiones de escritura.
* **Ciclo de Limpieza:** Los archivos temporales se eliminan automáticamente del almacenamiento local una vez que la reproducción ha finalizado.
* **Abstracción de Configuración:** Los parámetros sensibles (nombres de usuario, palabras clave y credenciales) se gestionan exclusivamente mediante variables de entorno local (.env).

## Instalación y Configuración

### Requisitos Previos
* Python 3.10 o superior.
* Servidor de inferencia local activo.

### Pasos de Instalación
1. Clonar el repositorio.
2. Instalar las dependencias necesarias:
   ```bash
   pip install -r requirements.txt

### Configuración del Archivo .env
Cree un archivo llamado .env en la raíz del proyecto. Este archivo está excluido del control de versiones por seguridad. Debe contener los siguientes parámetros:
TIKTOK_NICKNAME=id_de_usuario
BOT_NAME_PRIMARY=palabra_clave_1
BOT_NAME_SECONDARY=palabra_clave_2

### Ejecución
Para iniciar el sistema, ejecute el script principal:
python bot.py

## Gestión de QA y Control de Versiones
Este proyecto sigue prácticas de estandarización para asegurar que la lógica de filtrado y la reproducción de audio no presenten condiciones de carrera (race conditions) durante periodos de alta actividad en el flujo de datos. Se recomienda verificar que la carpeta audios/ tenga permisos de escritura antes de la ejecución.

### Detalles técnicos corregidos:
* **Punto 3:** Incluida la configuración de variables de entorno.
* **Punto 4:** Incluido el comando de ejecución.
* **QA Note:** Se añadió la nota sobre permisos de escritura en la carpeta de audios, que es un error común en entornos de pruebas.
