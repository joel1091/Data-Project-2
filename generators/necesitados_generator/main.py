import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromPubSub
from apache_beam.io.gcp.firestoreio import WriteToFirestore
from google.cloud import firestore
import json

class ProcessMessage(beam.DoFn):
    def process(self, element):
        # Decodificar el mensaje de Pub/Sub
        message = element.decode('utf-8')
        data = json.loads(message)
        
        # Aquí puedes agregar cualquier lógica de procesamiento adicional
        # Por ejemplo, transformar los datos, validarlos, etc.
        
        # Convertir el diccionario a un formato compatible con Firestore
        firestore_document = {
            'id': data['id'],
            'nombre': data['nombre'],
            'ubicacion': data['ubicacion'],
            'poblacion': data['poblacion'],
            'etiqueta': data['etiqueta'],
            'descripcion': data['descripcion'],
            'created_at': data['created_at'],
            'nivel_urgencia': data['nivel_urgencia'],
            'telefono': data['telefono']
        }
        
        yield firestore_document

def run():
    # Configuración del pipeline
    pipeline_options = PipelineOptions(
        project='steam-circlet-447114-h5',
        region='europe-west1',
        streaming=True,
        save_main_session=True
    )

    with beam.Pipeline(options=pipeline_options) as p:
        (p
         | 'Read from Pub/Sub' >> ReadFromPubSub(subscription='projects/steam-circlet-447114-h5/subscriptions/necesitados-events-sub')
         | 'Process Message' >> beam.ParDo(ProcessMessage())
         | 'Write to Firestore' >> WriteToFirestore(
             project='steam-circlet-447114-h5',
             collection='necesitados',
             id_field='id'
         )
        )

if __name__ == '__main__':
    run()