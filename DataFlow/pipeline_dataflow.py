import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.metrics import Metrics
# from google.cloud import firestore
from apache_beam.io.gcp.bigquery import WriteToBigQuery

from datetime import datetime
import argparse
import logging
import json
import math


# Decode messages from Pub/Sub
def ParsePubSubMessage(message):
    pubsub_message = message.decode('utf-8')
    msg = json.loads(pubsub_message)

    return msg['categoria'], msg

def RemoveDistance(data_list):
    for record in data_list:
        if 'distance' in record:
            del record['distance']
    return data_list

# Convert tuple to dict
def flatten_tuple(element):
    category, data = element
    request = data.get('request', {})
    volunteer = data.get('volunteer', {})
    yield {
#-------------------------- meter ID del match = > JOEL
            "category": category,
            "request_id": request.get("id"),
            "request_nombre": request.get("nombre"),
            "request_ubicacion": request.get("ubicacion"),
            "request_poblacion": request.get("poblacion"),
            "request_descripcion": request.get("descripcion"),
            "request_created_at": request.get("created_at"),
            "request_nivel_urgencia": request.get("nivel_urgencia"),
            "request_telefono": request.get("telefono"),
            "volunteer_id": volunteer.get("id"),
            "volunteer_nombre": volunteer.get("nombre"),
            "volunteer_ubicacion": volunteer.get("ubicacion"),
            "volunteer_poblacion": volunteer.get("poblacion"),
            "volunteer_radio_disponible_km": volunteer.get("radio_disponible_km"),
            "volunteer_created_at": volunteer.get("created_at"),
            "distance": data.get("distance"),
        }

table_bq_schema = {
#-------------------------- meter ID del match = > JOEL
    "fields": [
        {"name": "category", "type": "STRING", "mode": "REQUIRED"},
        {"name": "request_id", "type": "STRING", "mode": "NULLABLE"},
        {"name": "request_nombre", "type": "STRING", "mode": "NULLABLE"},
        {"name": "request_ubicacion", "type": "STRING", "mode": "NULLABLE"},
        {"name": "request_poblacion", "type": "STRING", "mode": "NULLABLE"},
        {"name": "request_descripcion", "type": "STRING", "mode": "NULLABLE"},
        {"name": "request_created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
        {"name": "request_nivel_urgencia", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "request_telefono", "type": "STRING", "mode": "NULLABLE"},
        {"name": "volunteer_id", "type": "STRING", "mode": "NULLABLE"},
        {"name": "volunteer_nombre", "type": "STRING", "mode": "NULLABLE"},
        {"name": "volunteer_ubicacion", "type": "STRING", "mode": "NULLABLE"},
        {"name": "volunteer_poblacion", "type": "STRING", "mode": "NULLABLE"},
        {"name": "volunteer_radio_disponible_km", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "volunteer_created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
        {"name": "distance", "type": "FLOAT", "mode": "NULLABLE"}
    ]
}


# Store in Firestore the messages that have not been matched by category
# Reused for the not matched by distance
# class StoreFirestoreNotMatched(beam.DoFn):

#     def __init__(self,firestore_collection):
#         self.firestore_collection = firestore_collection

#     def process(self, element):
#         db = firestore.Client()
#         events = ['request', 'volunteer']
#         category, (help_data, volunteer_data) = element

#         for event in events:
#             data_list = volunteer_data if event == 'volunteer' else help_data

#             if data_list:
#                 for record in data_list:
#                     try:
#                         doc_id = record.get('created_at', '')
#                         if doc_id:
#                             db.collection(self.firestore_collection).document('not_found').collection(event).document(doc_id).set(record)
#                             # logging.info(f"Stored {event} record in Firestore")
#                     except Exception as err:
#                         logging.error(f"Error storing {event}: {err}")


# Filter by distance
class FilterbyDistance(beam.DoFn):

    @staticmethod
    # Calculate distance based on coordinates
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radio de la Tierra en km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  
    
    # Filter by distance according to "radio_disponible_km" & tag not_matched_users and matched_users
    def process(self, element):
        category, (help_data, volunteer_data) = element

        for volunteer in volunteer_data:
            lat_volunteer, lon_volunteer = map(float, volunteer['ubicacion'].split(','))
            radio_max = volunteer.get('radio_disponible_km')

            if radio_max is None:
                radio_max = 100 ## TBD

            for request in help_data:
                lat_request, lon_request = map(float, request['ubicacion'].split(','))
                distance = self.haversine(lat_volunteer, lon_volunteer, lat_request, lon_request)
                
                data = (category, {"request": request,
                                    "volunteer": volunteer,
                                    "distance": distance
                                    })
                
                if distance <= radio_max:
                    yield data
                    yield beam.pvalue.TaggedOutput("matched_users", data)
                    logging.info(f"Match found: {data}")  
                else:
                    yield beam.pvalue.TaggedOutput("not_matched_users", data)
                    # logging.info(f"Match NOT found: {data}")  



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
    
    # parser.add_argument(
    #             '--firestore_collection',
    #             required=False,
    #             help='The Firestore collection where requests data will be stored.')
    
    parser.add_argument(
                '--bigquery_dataset',
                required=True,
                help='The BigQuery dataset where matched users will be stored.')
    
    parser.add_argument(
                '--output_topic',
                required=True,
                help='PubSub Topic for matched users.')
    

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
                | "Parse JSON help messages" >> beam.Map(ParsePubSubMessage)
                | "Sliding Window for help data" >> beam.WindowInto(beam.window.SlidingWindows(60, 5)) ## timing TBD
        )

        volunteer_data = (
            p
                | "Read volunteer data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.volunteers_subscription)
                | "Parse JSON volunteer messages" >> beam.Map(ParsePubSubMessage)
                | "Sliding Window for volunteer data" >> beam.WindowInto(beam.window.SlidingWindows(60, 5)) ## timing TBD
        )

        # CoGroupByKey
        grouped_data = (help_data, volunteer_data) | "Merge PCollections" >> beam.CoGroupByKey()

        # Partitions: 1) category_grouped: a match by category has been found 2) category_not_grouped: category has not been matched.
        category_grouped, category_not_grouped = (
            grouped_data | "Partition by volunteer found" >> beam.Partition(lambda kv, _: 0 if len(kv[1][0]) and len(kv[1][1]) > 0 else 1, 2) # 2 = number of partitions
        )

        # Partition 2: not grouped by category resend to PubSub


        # Partition 1: continues the Pipeline = Match by distance & Tagged Output
        filtered_data = ( 
            category_grouped
            | "Filter by distance" >> beam.ParDo(FilterbyDistance()).with_outputs("matched_users", "not_matched_users")
        )
        
        # Store matched users to BigQuery
        bq_data = (
            filtered_data.matched_users
                | "Flatten Tuple to Dict" >> beam.Map(flatten_tuple)
                | "Send matched_users to BigQuery" >> beam.io.WriteToBigQuery(
                    table=f"{args.project_id}:{args.bigquery_dataset}.matched_users", 
                    schema=table_bq_schema,
                    create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                    write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
                )
        bq_data | "debug bq" >> beam.Map(lambda x: logging.info({x}))
        
        # Public to output topic
        # output_data = (
        #     filtered_data.matched_users
        #     | "Write to PubSub topic Output" >> beam.io.WriteToPubSub(topic=args.output_topic)
        # )
        
        # Separate data to store in Firestore and enable reprocessing
        reprocess_data = (
            filtered_data.not_matched_users
                | "Remove distance" >> beam.Map(RemoveDistance)
                | "Separate help and volunteer" >> beam.FlatMap(lambda z: [
                    (z[0], ([z[1].get('request', {})], [])),
                    (z[0], ([], [z[1].get('volunteer', {})]))
                ])
# ------------------------- AÑADIR FUNCIÓN CONTADOR
                # | "Resend not matched by distance to PubSub topic output" >>
        )



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("The process started")

    run()