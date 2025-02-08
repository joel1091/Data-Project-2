# launcher/manual/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación
COPY ../../ .

# Cambia el directorio de trabajo 
WORKDIR /app/launcher/manual

# Ejecuta el main para modo manual
CMD ["python", "main.py"]
