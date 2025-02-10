import streamlit as st
from google.cloud import pubsub_v1
import uuid
from datetime import datetime
import json
import re

# Configuración de Pub/Sub
project_id = 'steam-circlet-447114-h5'
topic_id = 'ayudantes-events'  # Tópico de ayudantes

# Inicializar el cliente de Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

# Función para enviar datos a Pub/Sub
def enviar_a_pubsub(data):
    try:
        data_json = json.dumps(data, ensure_ascii=False)
        data_bytes = data_json.encode('utf-8')
        future = publisher.publish(topic_path, data=data_bytes)
        future.result()  # Esperar a que se confirme la publicación
        st.success("Datos enviados correctamente.")
    except Exception as e:
        st.error(f"Error al enviar datos: {e}")

st.title("Formulario de Ofrecimiento de Ayuda")

# Recopilación de datos
nombre = st.text_input("Nombre Completo")

# Crear dos columnas para latitud y longitud
col1, col2 = st.columns(2)

with col1:
    latitud = st.number_input("Latitud", format="%.4f")

with col2:
    longitud = st.number_input("Longitud", format="%.4f")

poblacion = st.text_input("Población")

# Lista de categorías
categorias = ["Selecciona la categoría", "Alimentos", "Medicamentos", "Limpieza", "Maquinaria", "Transporte", "Asistencia Social"]
categoria = st.selectbox("Categoría", categorias, index=0)

radio_disponible_km = st.number_input("Radio de Disponibilidad (km)", min_value=1)

# Enviar los datos al hacer clic en el botón
if st.button("Enviar Oferta de Ayuda"):
    if all([nombre, latitud, longitud, poblacion, categoria != "Selecciona la categoría", radio_disponible_km]):

        id_solicitud = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        data = {
            'id': id_solicitud,
            'nombre': nombre,
            'ubicacion': f"{latitud},{longitud}",
            'poblacion': poblacion,
            'categoria': categoria,
            'radio_disponible_km': radio_disponible_km,
            'created_at': created_at
        }

        enviar_a_pubsub(data)
    else:
        st.error("Por favor, complete todos los campos y asegúrese de seleccionar una categoría y un radio de disponibilidad.")
