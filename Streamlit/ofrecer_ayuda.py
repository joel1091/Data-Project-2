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
from folium import plugins

# Configuración de Pub/Sub
project_id = '<GCP_PROJECT_ID>'
topic_id = 'ayudantes-events'  

# Inicializar el cliente de Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

# Geolocalizador de OpenStreetMap (Para transformar de coordenadas a nombre de pueblo)
geolocator = Nominatim(user_agent="geoapi")

def obtener_pueblo(lat, lon):
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True)
        if location and 'address' in location.raw:
            return location.raw['address'].get('village') or location.raw['address'].get('town') or location.raw['address'].get('city', 'Desconocido')
        return "Desconocido"
    except Exception:
        return "Error obteniendo nombre"

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

def mostrar():
    st.title("Formulario de Ofrecimiento de Ayuda")

    # Inicializar session_state si no existe
    if "lat" not in st.session_state:
        st.session_state.lat = None
        st.session_state.lon = None
        st.session_state.pueblo = ""
        st.session_state.zoom = 11  
        st.session_state.center = [39.46, -0.45]

    # Inicializar el radio primero con el slider
    radio_disponible_km = st.slider(
        "Radio de Disponibilidad (km)", 
        min_value=1, 
        max_value=100, 
        value=10,
        step=1, 
        help="Desliza para seleccionar el radio de disponibilidad en kilómetros",
        key="radio"
    )

    # Crear el mapa manteniendo la vista guardada (VL)
    m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)

    # Agregar marcador si hay coordenadas seleccionadas
    if st.session_state.lat and st.session_state.lon:
        folium.Marker(
            location=[st.session_state.lat, st.session_state.lon],
            icon=folium.Icon(icon="map-marker", color="red"),
        ).add_to(m)
        
        # Añadir círculo para mostrar el radio de disponibilidad
        folium.Circle(
            location=[st.session_state.lat, st.session_state.lon],
            radius=radio_disponible_km * 1000,  # Convertir km a metros
            color="red",
            fill=True,
            fillColor="red",
            fillOpacity=0.2
        ).add_to(m)

    # Mostrar el mapa y capturar los clicks
    map_data = st_folium(m, width=800, height=400, key="map")

    # Actualizar coordenadas cuando se hace clic en el mapa
    if map_data and 'last_clicked' in map_data and map_data['last_clicked']:
        st.session_state.lat = map_data['last_clicked']['lat']
        st.session_state.lon = map_data['last_clicked']['lng']

        # Obtener el nombre del pueblo automáticamente
        st.session_state.pueblo = obtener_pueblo(st.session_state.lat, st.session_state.lon)

        # Mantener la vista actual
        if 'zoom' in map_data:
            st.session_state.zoom = map_data['zoom']
        if 'center' in map_data:
            st.session_state.center = [map_data['center']['lat'], map_data['center']['lng']]

        st.rerun()  # 🔄 Recargar la app para actualizar la información

    # Recopilación de datos
    col1, col2 = st.columns(2)

    with col1:
        latitud = st.text_input("Latitud", value=str(round(st.session_state.lat, 6)) if st.session_state.lat else "", disabled=True)

    with col2:
        longitud = st.text_input("Longitud", value=str(round(st.session_state.lon, 6)) if st.session_state.lon else "", disabled=True)

    poblacion = st.text_input("Población", value=st.session_state.pueblo, disabled=True)

    nombre = st.text_input("Nombre Completo")

    categorias = ["Selecciona la categoría", "Alimentos", "Medicamentos", "Limpieza", "Maquinaria", "Transporte", "Asistencia Social"]
    categoria = st.selectbox("Categoría", categorias, index=0)

    # Enviar los datos al hacer clic en el botón
    if st.button("Enviar Oferta de Ayuda"):
        if not st.session_state.lat or not st.session_state.lon:
            st.error("Por favor, seleccione una ubicación en el mapa.")
        elif all([nombre, latitud, longitud, poblacion, categoria != "Selecciona la categoría", radio_disponible_km]):
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
    
    if st.button("Volver al inicio"):
        st.session_state.pagina = "inicio"