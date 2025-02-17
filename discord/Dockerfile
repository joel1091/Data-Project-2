# Usa una imagen base de Python
FROM python:3.10-slim

WORKDIR /app

# Copia e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente
COPY main.py .

# El entrypoint es la función notify_discord definida en main.py
CMD ["main.notify_discord"]
