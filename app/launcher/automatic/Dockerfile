# launcher/automatic/Dockerfile
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos y lo instala
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia los archivos de la aplicación
COPY ../../ .

# Establece el directorio de trabajo 
WORKDIR /app/launcher/automatic

# Ejecuta el main para modo automático
CMD ["python", "main.py"]
