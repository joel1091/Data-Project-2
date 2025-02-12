import streamlit as st
from google.cloud import pubsub_v1
import uuid
from datetime import datetime
import json
import re
import folium
from streamlit_folium import folium_static, st_folium
from folium.plugins import MousePosition

# Configuración de Pub/Sub
project_id = '<PROJECT_ID>' 
topic_id = 'necesitados-events'  

# Inicializar el cliente de Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

# Función para enviar datos a Pub/Sub
def enviar_a_pubsub(data):
    try:
        data_json = json.dumps(data, ensure_ascii=False)
        data_bytes = data_json.encode('utf-8')
        future = publisher.publish(topic_path, data=data_bytes)
        future.result()
        st.success("Datos enviados correctamente.")
    except Exception as e:
        st.error(f"Error al enviar datos: {e}")

def mostrar():
    st.title("Formulario de Solicitud de Ayuda")

    m = folium.Map(location=[39.46, -0.45], zoom_start=11)
    
    # Agregar el plugin para mostrar coordenadas al mover el mouse
    formatter = "function(num) {return L.Util.formatNum(num, 5);};"
    MousePosition(
        position='topright',
        separator=' | ',
        empty_string='NaN',
        lng_first=True,
        num_digits=20,
        prefix='Coordenadas:',
        lat_formatter=formatter,
        lng_formatter=formatter,
    ).add_to(m)

    # Mostrar el mapa y capturar los clicks
    st.write("Haz clic en el mapa para seleccionar la ubicación:")
    map_data = st_folium(m, width=800, height=400)

    # Variables para almacenar las coordenadas
    lat = None
    lon = None

    # Actualizar coordenadas cuando se hace clic en el mapa
    if map_data['last_clicked']:
        lat = map_data['last_clicked']['lat']
        lon = map_data['last_clicked']['lng']

    # Recopilación de datos
    nombre = st.text_input("Nombre Completo")

    col1, col2 = st.columns(2)

    with col1:
        latitud = st.text_input("Latitud", value=str(round(lat, 6)) if lat else "", disabled=True)

    with col2:
        longitud = st.text_input("Longitud", value=str(round(lon, 6)) if lon else "", disabled=True)

    poblacion = st.text_input("Población")

    etiquetas = ["Selecciona el tipo de problema", "Alimentos", "Medicamentos", "Limpieza", "Maquinaria", "Transporte", "Asistencia Social"]
    etiqueta = st.selectbox("Etiqueta", etiquetas, index=0)

    descripcion = st.text_area("Descripción")
    nivel_urgencia = st.slider("Nivel de Urgencia", 1, 5)

    telefono = st.text_input("Teléfono")

    if telefono and not re.match(r'^\d{9}$', telefono):
        st.error("El número de teléfono debe tener exactamente 9 dígitos numéricos.")

    # Enviar datos al hacer clic en el botón
    if st.button("Enviar Solicitud"):
        if not lat or not lon:
            st.error("Por favor, seleccione una ubicación en el mapa.")
        elif all([nombre, latitud, longitud, poblacion, etiqueta != "Selecciona el tipo de problema", descripcion, telefono and re.match(r'^\d{9}$', telefono)]):
            id_solicitud = str(uuid.uuid4())
            created_at = datetime.now().isoformat()

            data = {
                'id': id_solicitud,
                'nombre': nombre,
                'ubicacion': f"{latitud},{longitud}",
                'poblacion': poblacion,
                'categoria': etiqueta,
                'descripcion': descripcion,
                'created_at': created_at,
                'nivel_urgencia': nivel_urgencia,
                'telefono': telefono
            }

            enviar_a_pubsub(data)
        else:
            st.error("Por favor, complete todos los campos y asegúrese de que el número de teléfono tenga exactamente 9 dígitos numéricos.")
    
    if st.button("Volver al inicio"):
        st.session_state.pagina = "inicio"