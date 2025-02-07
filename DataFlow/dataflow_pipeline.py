import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import firestore
import json
import logging
import os


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "<Aqui va la ruta de tu archivo JSON de credenciales>"


def ParsePubSubMessage(message):
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)
    logging.info(f"Mensaje recibido: {msg}")
    return msg  

#Esta era la prueba que estaba haciendo, subir solo los archivos con urgencia mayor a 4
#Obviamente no es lo que buscamos, era para probar la ingesta de datos a firestore
def filter_urgency(message):
    return message.get('urgencia', 0) >= 4


def write_to_firestore(element):
    db = firestore.Client(project="steam-circlet-447114-h5")  
    doc_ref = db.collection("necesitados").document(element["id"])
    doc_ref.set(element)

def run():

    options = PipelineOptions(
        runner="DataflowRunner", 
        project="steam-circlet-447114-h5",
        temp_location="gs://prueba-dp25/temp",
        region="europe-west1",
        streaming=True,
        max_num_workers=1,
    )

    with beam.Pipeline(options=options) as p:
        (p
         | "Leer desde Pub/Sub" >> beam.io.ReadFromPubSub(subscription="projects/steam-circlet-447114-h5/subscriptions/necesitados-events-sub")
         | "Parsear mensaje" >> beam.Map(ParsePubSubMessage)
         | "Filtrar por urgencia" >> beam.Filter(filter_urgency)  
         | "Escribir en Firestore" >> beam.Map(write_to_firestore) 
        )

if __name__ == "__main__":
    run()
