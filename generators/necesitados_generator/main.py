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
        # Zona 1: Ejemplo de área afectada
        {"lat_min": 39.30, "lat_max": 39.40, "lon_min": -0.45, "lon_max": -0.35},
        # Zona 2: Otra área potencialmente afectada
        {"lat_min": 39.35, "lat_max": 39.45, "lon_min": -0.50, "lon_max": -0.40},
        # Zona 3: Área adicional de afectación
        {"lat_min": 39.25, "lat_max": 39.35, "lon_min": -0.55, "lon_max": -0.45}
    ]
    zone = random.choice(dana_zones)
    lat = round(random.uniform(zone["lat_min"], zone["lat_max"]), 6)
    lon = round(random.uniform(zone["lon_min"], zone["lon_max"]), 6)
    return f"{lat},{lon}"

def get_random_necesitado():
    """
    Genera datos del necesitado usando la API de randomuser.me.
    La ubicación se genera usando zonas afectadas por la DANA.
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

    necesitado = {
        "id": str(uuid.uuid4()),
        "nombre": f"{user['name']['first']} {user['name']['last']}",
        "telefono": user["phone"],
        "ubicacion": generate_dana_coordinates(),  # Ubicación en zona DANA
        "descripcion": random.choice([
            "Necesito ayuda urgente.",
            "Requiero asistencia para una situación complicada.",
            "Estoy en busca de apoyo.",
            "Solicito ayuda para resolver un problema."
        ]),
        "nivel_urgencia": random.randint(1,5),
        "category": random.choice(["agua", "alimentos", "electricidad", "salud"]),
        "created_at": datetime.datetime.now().isoformat()
    }
    return necesitado

def get_manual_input_necesitado():
    """
    Permite al usuario ingresar manualmente los datos del necesitado.
    La foto es opcional: si se proporciona, se sube a Storage.
    La ubicación se genera usando zonas afectadas por la DANA.
    """
    necesitado = {}
    necesitado["id"] = str(uuid.uuid4())
    necesitado["nombre"] = input("Ingrese nombre: ")
    necesitado["telefono"] = input("Ingrese teléfono: ")
    # Usamos generate_dana_coordinates para simular ubicación realista en zonas DANA
    necesitado["ubicacion"] = generate_dana_coordinates()
    necesitado["descripcion"] = input("Ingrese una descripción: ")
    necesitado["nivel_urgencia"] = int(input("Ingrese nivel de urgencia (1-5): "))
    necesitado["category"] = input("Ingrese categoría: ")
    necesitado["created_at"] = datetime.datetime.now().isoformat()
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
