import uuid
import datetime
import json
import requests
import random
import os
import time
import threading
import re
from google.cloud import pubsub_v1
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

# Diccionario de categorías con descripciones (separando Maquinaria y Transporte)
categorias = {
    "Alimentos": [
        "Necesito agua potable y alimentos no perecederos.",
        "Necesito pañales y leche en polvo para bebés.",
        "Necesito alimentos sin gluten para celíacos.",
        "Necesito comida especial para diabéticos.",
        "Necesito frutas y verduras frescas.",
        "Necesito alimentos para mascotas (perros, gatos, etc.).",
        "Necesito ayuda con la distribución de alimentos en mi zona."
    ],
    "Medicamentos": [
        "Necesito medicamentos urgentes (especificar).",
        "Necesito insulina o medicación para la diabetes.",
        "Necesito medicamentos para la presión arterial.",
        "Necesito antibióticos o antiinflamatorios.",
        "Necesito inhaladores para personas asmáticas.",
        "Necesito material de primeros auxilios (vendas, desinfectante, gasas, etc.).",
        "Necesito asistencia para conseguir recetas médicas urgentes."
    ],
    "Limpieza": [
        "Necesito productos de higiene personal y limpieza.",
        "Necesito ayuda para limpiar mi vivienda afectada por la inundación.",
        "Necesito ayuda para retirar agua de mi casa/local.",
        "Necesito desinfectantes para prevenir enfermedades.",
        "Necesito detergentes y productos para lavar ropa afectada por el agua."
    ],
    "Maquinaria": [
        "Necesito reparación urgente en mi hogar (electricidad, fontanería, etc.).",
        "Necesito ayuda para retirar escombros o muebles dañados.",
        "Necesito herramientas y equipos para realizar reparaciones en viviendas afectadas."
    ],
    "Transporte": [
        "Necesito transporte para ir al hospital o centro de salud.",
        "Necesito transporte para desplazarme a un refugio o casa de familiares."
    ],
    "Asistencia Social": [
        "Hay personas mayores/niños en mi hogar que necesitan asistencia urgente.",
        "Necesito ayuda para una persona con movilidad reducida.",
        "Necesito atención psicológica o emocional.",
        "Necesito un lugar temporal donde alojarme.",
        "Necesito información sobre refugios y albergues disponibles.",
        "Necesito información sobre cómo solicitar ayudas económicas o materiales.",
        "Necesito contactar con voluntarios que puedan ayudar en mi zona.",
        "Necesito ayuda con mascotas afectadas por la DANA.",
        "Necesito asesoramiento para reconstruir mi vivienda."
    ]
}

# Cargar variables de entorno
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
TOPIC_NECESITADOS = "necesitados-events"

def publish_message(topic, message):
    """
    Publica el mensaje en el tópico de Pub/Sub.
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, topic)
    future = publisher.publish(topic_path, message.encode("utf-8"))
    print(f"Mensaje publicado en {topic_path}: {future.result()}")

def generate_dana_coordinates():
    """
    Genera coordenadas aleatorias dentro de zonas afectadas por la DANA.
    Se selecciona aleatoriamente entre varias zonas predefinidas (con límites aproximados).
    """
    dana_zones = [
        {"lat_min": 39.30, "lat_max": 39.40, "lon_min": -0.45, "lon_max": -0.35},
        {"lat_min": 39.35, "lat_max": 39.45, "lon_min": -0.50, "lon_max": -0.40},
        {"lat_min": 39.25, "lat_max": 39.35, "lon_min": -0.55, "lon_max": -0.45}
    ]
    zone = random.choice(dana_zones)
    lat = round(random.uniform(zone["lat_min"], zone["lat_max"]), 6)
    lon = round(random.uniform(zone["lon_min"], zone["lon_max"]), 6)
    return f"{lat},{lon}"

def generar_telefono_movil():
    """
    Genera un número de teléfono móvil español de 9 dígitos.
    """
    return random.choice(['6', '7']) + ''.join([str(random.randint(0, 9)) for _ in range(8)])

def reverse_geocode(lat, lon):
    """
    Utiliza geopy con Nominatim para convertir latitud y longitud en el nombre de una población.
    """
    geolocator = Nominatim(user_agent="necesitado_geocoder")
    try:
        time.sleep(1)  # Respeta los límites de uso de Nominatim
        location = geolocator.reverse((lat, lon), language="es")
        if location and location.raw and "address" in location.raw:
            address = location.raw["address"]
            return address.get("city") or address.get("town") or address.get("village")
    except Exception as e:
        print("Error en reverse geocoding:", e)
    return None

def get_random_necesitado():
    """
    Genera datos del necesitado usando la API de randomuser.me.
    La ubicación se genera usando zonas afectadas por la DANA y se realiza reverse geocoding.
    """
    url = "https://randomuser.me/api/"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print("Error al llamar a randomuser.me:", e)
        return None
    data = response.json()
    user = data["results"][0]
    etiqueta = random.choice(list(categorias.keys()))
    
    coords = generate_dana_coordinates()  
    try:
        lat_str, lon_str = coords.split(',')
        poblacion = reverse_geocode(float(lat_str), float(lon_str))
    except Exception as e:
        print("Error al realizar reverse geocoding en modo automático:", e)
        poblacion = ""
    
    necesitado = {
        "id": str(uuid.uuid4()),
        "nombre": f"{user['name']['first']} {user['name']['last']}",
        "ubicacion": coords,
        "poblacion": poblacion if poblacion else "",
        "etiqueta": etiqueta,
        "descripcion": random.choice(categorias[etiqueta]),
        "created_at": datetime.datetime.now().isoformat(),
        "nivel_urgencia": random.randint(1, 5),
        "telefono": generar_telefono_movil()
    }
    return necesitado

def get_manual_input_necesitado():
    """
    Permite al usuario ingresar manualmente los datos del necesitado.
    Se permite ingresar la ubicación en formato 'lat,lon' y se realiza reverse geocoding para obtener el nombre de la población.
    """
    etiquetas_validas = ["Alimentos", "Medicamentos", "Limpieza", "Maquinaria", "Transporte", "Asistencia Social"]

    while True:
        nombre = input("Ingrese nombre: ").strip()
        if nombre:
            break
        print("Error: El nombre no puede estar vacío. Intente de nuevo.")

    # Ingresar manualmente la ubicación
    while True:
        ubicacion = input("Ingrese ubicación (coordenadas) en formato 'lat,lon': ").strip()
        if ubicacion:
            try:
                lat_str, lon_str = ubicacion.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
            except Exception as e:
                print("Error: Formato de ubicación incorrecto. Use 'lat,lon'.")
                continue
            break
        print("Error: La ubicación no puede estar vacía. Intente de nuevo.")

    # Realizar reverse geocoding para obtener el nombre de la población
    poblacion = reverse_geocode(lat, lon)

    while True:
        etiqueta = input(f"Ingrese etiqueta {etiquetas_validas}: ").strip()
        if etiqueta in etiquetas_validas:
            break
        print(f"Error: La etiqueta debe ser una de las siguientes: {etiquetas_validas}. Intente de nuevo.")

    while True:
        descripcion = input("Ingrese una descripción: ").strip()
        if descripcion:
            break
        print("Error: La descripción no puede estar vacía. Intente de nuevo.")

    while True:
        try:
            urgencia = int(input("Ingrese nivel de urgencia (1-5): ").strip())
            if 1 <= urgencia <= 5:
                break
            else:
                print("Error: La urgencia debe estar entre 1 y 5. Intente de nuevo.")
        except ValueError:
            print("Error: La urgencia debe ser un número entero. Intente de nuevo.")

    while True:
        telefono = input("Ingrese su número de teléfono móvil (9 dígitos): ").strip()
        if re.fullmatch(r"\d{9}", telefono):
            break
        print("Error: El número de teléfono debe tener exactamente 9 dígitos numéricos. Intente de nuevo.")

    necesitado = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "ubicacion": ubicacion,
        "poblacion": poblacion if poblacion else "",
        "etiqueta": etiqueta,
        "descripcion": descripcion,
        "created_at": datetime.datetime.now().isoformat(),
        "urgencia": urgencia,
        "telefono": telefono
    }
    return necesitado

def run_automatic_generator():
    """
    Genera mensajes de necesitados de forma automática en intervalos aleatorios.
    """
    while True:
        sleep_time = random.randint(5, 15)
        print(f"[Necesitados Automático] Esperando {sleep_time} segundos...")
        time.sleep(sleep_time)
        necesitado = get_random_necesitado()
        if necesitado:
            json_message = json.dumps(necesitado, indent=2, ensure_ascii=False)
            publish_message(TOPIC_NECESITADOS, json_message)

def run_manual_generator():
    """
    Permite ingresar manualmente los datos de un necesitado y publicarlos.
    """
    while True:
        opcion = input("¿Desea ingresar manualmente un necesitado? (s/n): ").strip().lower()
        if opcion == "s":
            necesitado = get_manual_input_necesitado()
            json_message = json.dumps(necesitado, indent=2, ensure_ascii=False)
            publish_message(TOPIC_NECESITADOS, json_message)
        else:
            salir = input("¿Desea salir del modo manual? (s/n): ").strip().lower()
            if salir == "s":
                break

def main():
    print("Generador de Necesitados")
    modo = input("Seleccione modo: (a)utomático, (m)anual, (b) ambos: ").strip().lower()
    if modo == "a":
        run_automatic_generator()
    elif modo == "m":
        run_manual_generator()
    elif modo == "b":
        thread_auto = threading.Thread(target=run_automatic_generator, daemon=True)
        thread_auto.start()
        run_manual_generator()
    else:
        print("Modo no reconocido. Saliendo.")

if __name__ == "__main__":
    main()