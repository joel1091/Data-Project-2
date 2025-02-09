# Dockerfile para el launcher automático
FROM python:3.10-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido de la carpeta actual (que es app/launcher/automatic) en /app
COPY . .

# Ejecuta el archivo main.py
CMD ["python", "main.py"]
