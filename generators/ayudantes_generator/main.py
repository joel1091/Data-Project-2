import uuid
import datetime
import json
import requests
import random
import os
import time
import threading
from google.cloud import pubsub_v1
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

# Cargar variables de entorno
load_dotenv()
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
TOPIC_AYUDANTES = "ayudantes-events"

def publish_message(topic, message):
    """
    Publica el mensaje en el tópico de Pub/Sub.
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, topic)
    future = publisher.publish(topic_path, message.encode("utf-8"))
    print(f"Mensaje publicado en {topic_path}: {future.result()}")

def generate_valencia_coordinates():
    """
    Genera coordenadas aleatorias dentro de la provincia de Valencia.
    """
    lat = round(random.uniform(39.0, 39.8), 6)
    lon = round(random.uniform(-0.8, -0.2), 6)
    return f"{lat},{lon}"

def reverse_geocode(lat, lon):
    """
    Utiliza geopy con Nominatim para convertir latitud y longitud en el nombre de una población.
    """
    geolocator = Nominatim(user_agent="ayudante_geocoder")
    try:
        time.sleep(1)  # Breve retraso para respetar límites de Nominatim
        location = geolocator.reverse((lat, lon), language="es")
        if location and location.raw and "address" in location.raw:
            address = location.raw["address"]
            return address.get("city") or address.get("town") or address.get("village")
    except Exception as e:
        print("Error en reverse geocoding:", e)
    return None

categorias = ["Alimentos", "Medicamentos", "Limpieza", "Maquinaria, Transporte", "Asistencia Social"]
radio_disponibilidad = [5, 10, 15, 50]

def get_random_ayudante():
    """
    Genera datos del ayudante usando la API de randomuser.me.
    La ubicación se genera usando coordenadas de la provincia de Valencia y se realiza reverse geocoding.
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
    
    coords = generate_valencia_coordinates()  # Ejemplo: "39.069883,-0.64334"
    try:
        lat_str, lon_str = coords.split(',')
        poblacion = reverse_geocode(float(lat_str), float(lon_str))
    except Exception as e:
        print("Error en reverse geocoding en modo automático:", e)
        poblacion = ""
    
    ayudante = {
        "id": str(uuid.uuid4()),
        "nombre": f"{user['name']['first']} {user['name']['last']}",
        "ubicacion": coords,
        "poblacion": poblacion if poblacion else "",
        "categoria": random.choice(categorias),
        "radio_disponible_km": random.choice(radio_disponibilidad),
        "created_at": datetime.datetime.now().isoformat()
    }
    return ayudante

def get_manual_input_ayudante():
    """
    Permite al usuario ingresar manualmente los datos de un ayudante.
    Se realiza reverse geocoding para traducir las coordenadas a un nombre de población.
    """
    while True:
        nombre = input("Ingrese nombre: ").strip()
        if nombre:
            break
        print("Error: El nombre no puede estar vacío. Intente de nuevo.")

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

    while True:
        etiqueta = input(f"Ingrese etiqueta {categorias}: ").strip()
        if etiqueta in categorias:
            break
        print(f"Error: La etiqueta debe ser una de las siguientes: {categorias}. Intente de nuevo.")

    while True:
        try:
            urgencia = int(input("Ingrese nivel de urgencia (1-5): ").strip())
            if 1 <= urgencia <= 5:
                break
            else:
                print("Error: La urgencia debe estar entre 1 y 5. Intente de nuevo.")
        except ValueError:
            print("Error: La urgencia debe ser un número entero. Intente de nuevo.")

    poblacion = reverse_geocode(lat, lon)
    ayudante = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "ubicacion": ubicacion,
        "poblacion": poblacion if poblacion else "",
        "categoria": etiqueta,
        "urgencia": urgencia,
        "created_at": datetime.datetime.now().isoformat()
    }
    return ayudante

def run_automatic_generator():
    """
    Genera mensajes de ayudantes de forma automática en intervalos aleatorios.
    """
    while True:
        sleep_time = random.randint(5, 15)
        print(f"[Ayudantes Automático] Esperando {sleep_time} segundos...")
        time.sleep(sleep_time)
        ayudante = get_random_ayudante()
        if ayudante:
            json_message = json.dumps(ayudante, indent=2, ensure_ascii=False)
            publish_message(TOPIC_AYUDANTES, json_message)

def run_manual_generator():
    """
    Permite ingresar datos de un ayudante manualmente y publicarlos.
    """
    while True:
        opcion = input("¿Desea ingresar manualmente un ayudante? (s/n): ").strip().lower()
        if opcion == "s":
            ayudante = get_manual_input_ayudante()
            json_message = json.dumps(ayudante, indent=2, ensure_ascii=False)
            publish_message(TOPIC_AYUDANTES, json_message)
        else:
            salir = input("¿Desea salir del modo manual? (s/n): ").strip().lower()
            if salir == "s":
                break

def main():
    print("Generador de Ayudantes")
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