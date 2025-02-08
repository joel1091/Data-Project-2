import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.metrics import Metrics
from google.cloud import firestore

from datetime import datetime
import argparse
import logging
import json
import math


# Decode messages from Pub/Sub
### !!! en ambos generadores, el campo no se llama igual, en uno categoria y en otro etiqueta, para facitarlo, cambiarlo?
def ParsePubSubMessage1(message):
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)

    return msg['etiqueta'], msg

def ParsePubSubMessage2(message):
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)

    return msg['categoria'], msg

# Filter by distance
class FilterbyDistance(beam.DoFn):

    @staticmethod
    # Calcular la distancia según las coordinadas
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radio de la Tierra en km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  
    
    # Filtrar por distancia cumpliendo "radio_disponible_km"
    def process(self, element):
        category, (help_data, volunteer_data) = element

        for volunteer in volunteer_data:
            lat_volunteer, lon_volunteer = map(float, volunteer['ubicacion'].split(','))
            radio_max = volunteer.get('radio_disponible_km')

            if radio_max is None:
                radio_max = 100

            for request in help_data:
                lat_request, lon_request = map(float, request['ubicacion'].split(','))
                distance = self.haversine(lat_volunteer, lon_volunteer, lat_request, lon_request)
                
                data = (category, {"volunteer": volunteer,
                                    "request": request,
                                    "distance": distance
                                    })
                
                if distance <= radio_max:
                    yield data

# Store in Firestore
class FormatFirestoreDocument(beam.DoFn):

    def __init__(self,mode,firestore_collection):
        self.mode = mode
        self.firestore_collection = firestore_collection

    def process(self, element):
        db = firestore.Client()
        events = ['category', 'volunteer','request'] if self.mode == 'raw' else ['category', 'volunteer','request','distance']

        for event in events:
            if event in element and len(element[event]) > 0:
                for record in element[event]:
                    try:
                        db.collection(self.firestore_collection).document('not_matched').collection(event).document(element[event]['created_at']).set(element[event])
                        logging.info(f"Record stored in Firestore.")
                    except Exception as err:
                        logging.error(f"Error storing: {err}")
        # else:
        #     try:
        #         db.collection(self.firestore_collection).document('matched').collection('data').document('created_at').set(element)
        #         logging.info(f"Record stored in Firestore for category {element['category']}")
        #     except Exception as err:
        #         logging.error(err)
    


# MATCH STATUS
class MatchedStatusDoFn(beam.DoFn):
    def process(self, element):
        category, (help_data, volunteer_data) = element
        
        distance = help_data.get('distance')

        matched_data = {
            "category": category,
            "volunteer": volunteer_data,
            "request": help_data,
            "distance": distance
        }

        if volunteer_data["categoria"] == help_data["etiqueta"] and distance <= volunteer_data["radio_disponible_km"]:
            yield beam.pvalue.TaggedOutput("matched_users", matched_data)
        else:
            yield beam.pvalue.TaggedOutput("not_matched_users", matched_data)


def run():
    parser = argparse.ArgumentParser(description=('Input arguments for the Dataflow Streaming Pipeline.'))

    parser.add_argument(
                '--project_id',
                required=True,
                help='GCP cloud project name.')
    
    parser.add_argument(
                '--help_subscription',
                required=True,
                help='PubSub subscription used for reading help requests data.')
    
    
    parser.add_argument(
                '--volunteers_subscription',
                required=True,
                help='PubSub subscription used for reading volunteers data.')
    
    parser.add_argument(
                '--firestore_collection',
                required=True,
                help='The Firestore collection where requests data will be stored.')
    
    # parser.add_argument(
    #             '--output_topic',
    #             required=True,
    #             help='PubSub Topic for sending push notifications.')
    
    # parser.add_argument(
    #             '--system_id',
    #             required=False,
    #             help='System that evaluates the telemetry data of the car.')

    args, pipeline_opts = parser.parse_known_args()

## PIPELINE
    # Pipeline Options
    options = PipelineOptions(pipeline_opts,
            save_main_session=True, streaming=True, project=args.project_id)
    
    # Pipeline Object
    with beam.Pipeline(argv=pipeline_opts,options=options) as p:

        help_data = (
            p
                | "Read help data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.help_subscription)
                | "Parse JSON help messages" >> beam.Map(ParsePubSubMessage1)

                # Mirar qué tipo de window nos conviene más, sliding o sessions creo que encajan más para nuestro caso
                # - Sliding: si una no hace match en una window, posibilidad en la siguiente
                # - Sessions:si no llegasen mensajes en X tiempo, cerrar la window para no "retrasar" la llegada de la ayuda

                | "Session Window for help data" >> beam.WindowInto(beam.window.Sessions(30))
        )

        volunteer_data = (
            p
                | "Read volunteer data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.volunteers_subscription)
                | "Parse JSON volunteer messages" >> beam.Map(ParsePubSubMessage2)
                | "Session Window for volunteer data" >> beam.WindowInto(beam.window.Sessions(30))
        )

        # CoGroupByKey
        grouped_data = (volunteer_data, help_data) | "Merge PCollections" >> beam.CoGroupByKey()

        # Partitions: 1) category_grouped: a match by category has been found 2) category_not_grouped: category has not been matched.
        
        category_grouped, category_not_grouped = (
            grouped_data | "Partition by volunteer found" >> beam.Partition(lambda kv, _: 0 if len(kv[1][0]) and len(kv[1][1]) > 0 else 1, 2)
        )
        ######## No salen o tardan en salir las category_grouped, no sé si es cosa de la window también.

        # category_grouped | "Debug category grouped data" >> beam.Map(lambda x: logging.info(f"Grouped data: {x}")) 
        # category_not_grouped | "Debug not grouped data" >> beam.Map(lambda x: logging.info(f"Not grouped data: {x}")) 

        send_not_grouped = (
            category_not_grouped
            | "Send not grouped messages to Firestore" >> beam.ParDo(FormatFirestoreDocument(mode='raw', firestore_collection=args.firestore_collection))
        )

        # Filter by distance
        # filtered_data = ( 
        #     category_grouped
        #     | "Filter by distance" >> beam.ParDo(FilterbyDistance())
        # )
        
        # processed_data = (
        #     filtered_data
        #     | "Check match status" >> beam.ParDo(MatchedStatusDoFn()).with_outputs("matched_users", "not_matched_users")
        # )
        # (
        #     processed_data.matched_users
        #         | "Write matched_users documents" >> beam.ParDo(FormatFirestoreocument(mode='raw', firestore_collection=args.firestore_collection))
        # )

        # resend_data = (
        #     processed_data.not_matched_users
        #         | 
        # )



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("The process started")

    run()