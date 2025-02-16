# Usa una imagen base ligera de Python
FROM python:3.9-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY main.py .

# Variables de entorno para el servidor
ENV PORT=8080

# Configura el usuario no root por seguridad
RUN useradd -m nonroot
USER nonroot

# Configura el comando para ejecutar la aplicación
# notify_discord es tu entry point
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "main:notify_discord"