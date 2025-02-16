import streamlit as st
from google.cloud import pubsub_v1
import uuid
from datetime import datetime
import json
import re
import folium
from streamlit_folium import st_folium
from folium.plugins import MousePosition
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import os


# Configuración de Pub/Sub
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
topic_id = 'ayudantes-events'

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, topic_id)


# Geolocalizador de OpenStreetMap (Para transformar de coordenadas a nombre de pueblo)
geolocator = Nominatim(user_agent="geoapi")

def obtener_pueblo(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True)
        if location and 'address' in location.raw:
            return location.raw['address'].get('village') or location.raw['address'].get('town') or location.raw['address'].get('city', 'Desconocido')
        return "Desconocido"
    except Exception as e:
        return "Error obteniendo nombre"

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

    # Inicializar variables en session_state
    if "lat" not in st.session_state:
        st.session_state.lat = None
        st.session_state.lon = None
        st.session_state.pueblo = ""  
        st.session_state.zoom = 11  
        st.session_state.center = [39.46, -0.45]  

    # Crear el mapa con la vista guardada (VL)
    m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)

    # Si ya hay una ubicación guardada, agregar marcador
    if st.session_state.lat and st.session_state.lon:
        folium.Marker(
            location=[st.session_state.lat, st.session_state.lon],
            icon=folium.Icon(icon="map-marker", color="red"),
        ).add_to(m)

    # Mostrar el mapa y capturar eventos
    map_data = st_folium(m, width=800, height=400, key="map")

    # Si el usuario hace clic en el mapa, actualizar coordenadas y obtener el nombre del pueblo
    if map_data and 'last_clicked' in map_data and map_data['last_clicked']:
        st.session_state.lat = map_data['last_clicked']['lat']
        st.session_state.lon = map_data['last_clicked']['lng']

        # Obtener el nombre del pueblo
        st.session_state.pueblo = obtener_pueblo(st.session_state.lat, st.session_state.lon)

        # Mantener la vista actual
        if 'zoom' in map_data:
            st.session_state.zoom = map_data['zoom']
        if 'center' in map_data:
            st.session_state.center = [map_data['center']['lat'], map_data['center']['lng']]

        st.rerun()  # 🔥 Recarga la app para actualizar el marcador y el nombre del pueblo

    # Mostrar coordenadas seleccionadas y el pueblo
    col1, col2 = st.columns(2)

    with col1:
        latitud = st.text_input("Latitud", value=str(round(st.session_state.lat, 6)) if st.session_state.lat else "", disabled=True)

    with col2:
        longitud = st.text_input("Longitud", value=str(round(st.session_state.lon, 6)) if st.session_state.lon else "", disabled=True)

    poblacion = st.text_input("Población", value=st.session_state.pueblo, disabled=True)

    nombre = st.text_input("Nombre Completo")
    etiquetas = ["Selecciona el tipo de problema", "Alimentos", "Medicamentos", "Limpieza", "Maquinaria", "Transporte", "Asistencia Social"]
    etiqueta = st.selectbox("Etiqueta", etiquetas, index=0)

    descripcion = st.text_area("Descripción")
    nivel_urgencia = st.slider("Nivel de Urgencia", 1, 5)
    telefono = st.text_input("Teléfono")

    if telefono and not re.match(r'^\d{9}$', telefono):
        st.error("El número de teléfono debe tener exactamente 9 dígitos numéricos.")

    if st.button("Enviar Solicitud"):
        if not st.session_state.lat or not st.session_state.lon:
            st.error("Por favor, seleccione una ubicación en el mapa.")
        elif all([nombre, latitud, longitud, poblacion, etiqueta != "Selecciona el tipo de problema", descripcion, telefono and re.match(r'^\d{9}$', telefono)]):
            id_solicitud = str(uuid.uuid4())
            created_at = datetime.now().isoformat()

            data = {
                'id': id_solicitud,
                'nombre': nombre,
                'ubicacion': f"{latitud},{longitud}",
                'poblacion': poblacion,  # Ahora se autocompleta con el nombre del pueblo
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
