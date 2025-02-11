# Usar una imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requerimientos y el script de la aplicación
COPY app.py .
COPY ofrecer_ayuda.py .
COPY pedir_ayuda.py .
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el que Streamlit ejecutará la aplicación
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.enableCORS", "false", "--browser.serverAddress", "0.0.0.0"]
