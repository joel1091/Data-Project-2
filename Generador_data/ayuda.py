import random
from datetime import datetime
import time

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
    "Maquinaria y Transporte": [
        "Necesito ayuda para mover mi coche averiado o inundado.",
        "Necesito reparación urgente en mi hogar (electricidad, fontanería, etc.).",
        "Necesito ayuda para retirar escombros o muebles dañados.",
        "Necesito transporte para ir al hospital o centro de salud.",
        "Necesito transporte para desplazarme a un refugio o casa de familiares.",
        "Necesito herramientas y equipos para realizar reparaciones en viviendas afectadas."
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

nombres = [
    "Álvaro Ferrer", "Marina Pérez", "Héctor García", "Carmen Torres", "Víctor Navarro",
    "Elena Ruiz", "Jordi Soriano", "Marta Gómez", "Pau Martínez", "Laia Serrano",
    "Iván Sanchis", "Nuria López", "Sergio Vidal", "Claudia Ibáñez", "Marc Ferrando",
    "Adriana Castelló", "Rubén Blasco", "Beatriz Pastor", "Óscar Doménech", "Aitana Montiel",
    "Samuel Calabuig", "Noelia Benavent", "Gabriel Soler", "Lucía Mira", "Xavier Cano",
    "Ana Llopis", "Raúl Vázquez", "Isabel Almenar", "Daniel Esteve", "Rosa Alcázar",
    "Hugo Beltrán", "Lorena Campos", "Eric Fuster", "Silvia Morera", "David Alcaraz",
    "Teresa Escrivà", "Joel Segarra", "Patricia Olmos", "Cristian Giner", "Sandra Roselló",
    "Manuel Carbonell", "Ester Climent", "Jaume Benlloch", "Sofía Palop", "Toni Forner",
    "Estela Ripoll", "Francesc Moya", "Verónica Cervera", "Andrés Planelles", "Raquel Jordà"
]


def generar_telefono_movil():

    return random.choice(['6', '7']) + ''.join([str(random.randint(0, 9)) for _ in range(8)])


# Generador de coordenadas aleatorias
def generar_coordenadas_aleatorias():
    lat_min, lat_max = 39.407, 39.507
    lon_min, lon_max = -0.435, -0.315
    return (random.uniform(lat_min, lat_max), random.uniform(lon_min, lon_max))

# Función para generar peticiones de ayuda
def generar_peticiones(n=1):
    peticiones = []
    global id_contador  # Variable global que cuenta el ID
    for _ in range(n):
        mensaje_id = id_contador 
        id_contador += 1  
        nombre = random.choice(nombres)  
        categoria_nombre = random.choice(list(categorias.keys()))  
        frase_aleatoria = random.choice(categorias[categoria_nombre]) 
        coordenadas = generar_coordenadas_aleatorias()  
        date = datetime.now()
        telefono = generar_telefono_movil()
        urgencia = random.choice([1, 10])

        peticion = {
            "ID": mensaje_id,
            "Nombre": nombre,
            "Coordenadas": coordenadas,
            "Frase": frase_aleatoria,
            "Categoría": categoria_nombre,
            "created_at": date,
            "Telefono": telefono,
            "Urgencia": urgencia
        }
        peticiones.append(peticion)

    return peticiones

# Inicializar el contador del ID
id_contador = 1 #En el caso de que ya hubiese 10 peticiones habría que modificar esto y compararlo con la base de datos. 
                #Suponemos que una vez que se reinicia el programa, se reinicia el contador y la BD se vacía.

# Imprimir 10 peticiones, si se quiere hacer infinito se usa un while true y ya está.
for peticion in generar_peticiones(10):
    print(f"ID: {peticion['ID']}, created_at: {peticion['created_at']}, Telefono: {peticion['Telefono']} , Nombre: {peticion['Nombre']}, Coordenadas: {peticion['Coordenadas']}, Urgencia: {peticion['Urgencia']} , Categoría: {peticion['Categoría']}, Frase: {peticion['Frase']}")
    
    time.sleep(5)