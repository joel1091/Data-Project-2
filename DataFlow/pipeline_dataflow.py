import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.metrics import Metrics
from google.cloud import bigquery
from apache_beam.io import WriteToPubSub

from datetime import datetime
import argparse
import logging
import json
import math
import uuid

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
    
# Clean message before resending to PubSub
def ConvertToBytes(element):
    cleaned_message = {}
    if element:
        for item in element:
            cleaned_message = item 
    # logging.info(f"Mensaje limpio: {cleaned_message}")
    message_bytes = json.dumps(cleaned_message).encode('utf-8')
    return message_bytes


# Count attempts, discard when > 5
class AddAttempts(beam.DoFn):
    def process(self, element):
        category, (help_data, volunteer_data) = element
        
        if help_data:
            for item in help_data:
                item["attempts"] = item.get("attempts", 0) + 1
                if item["attempts"] >= 5:
                    logging.info(f"Se ha alcanzado el límite de intentos para el mensaje del necesitado {item['id']}.")
                    return None

        if volunteer_data:
            for item in volunteer_data:
                item["attempts"] = item.get("attempts", 0) + 1
                if item["attempts"] >= 5:
                    logging.info(f"Se ha alcanzado el límite de intentos para el mensaje del voluntario {item['id']}.")
                    return None

        if help_data:
            # logging.info(f"Mensaje saliente: {element}")
            yield help_data
        if volunteer_data:
            # logging.info(f"Mensaje saliente voluntarios: {element}")
            yield volunteer_data
            

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
                    # logging.info(f"Match found: {data}")  
                else:
                    yield beam.pvalue.TaggedOutput("not_matched_users", data)
                    # logging.info(f"Match NOT found: {data}")  

# Setup BigQuery
class BigQuerySetup:
    def __init__(self, project_id, dataset_id):
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id
        self.project_id = project_id
        self.dataset_ref = f"{project_id}.{dataset_id}"

    def create_dataset_if_not_exists(self):
        """Crea el dataset si no existe."""
        try:
            dataset = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
            dataset.location = "EU"
            self.client.create_dataset(dataset, exists_ok=True)
            logging.info(f"Dataset {self.dataset_id} está listo")
        except Exception as e:
            logging.error(f"Error creando dataset: {e}")
            raise

    def create_tables_if_not_exist(self):
        """Crea todas las tablas necesarias si no existen."""
        # Schema para unmatched_requests
        requests_schema = [
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("nombre", "STRING"),
            bigquery.SchemaField("ubicacion", "STRING"),
            bigquery.SchemaField("poblacion", "STRING"),
            bigquery.SchemaField("categoria", "STRING"),
            bigquery.SchemaField("descripcion", "STRING"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("nivel_urgencia", "INTEGER"),
            bigquery.SchemaField("telefono", "STRING"),
            bigquery.SchemaField("insertion_timestamp", "TIMESTAMP")
        ]

        # Schema para unmatched_volunteers
        volunteers_schema = [
            bigquery.SchemaField("id", "STRING"),
            bigquery.SchemaField("nombre", "STRING"),
            bigquery.SchemaField("ubicacion", "STRING"),
            bigquery.SchemaField("poblacion", "STRING"),
            bigquery.SchemaField("categoria", "STRING"),
            bigquery.SchemaField("radio_disponible_km", "FLOAT"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("insertion_timestamp", "TIMESTAMP")
        ]

        # Schema para matched_pairs
        matched_pairs_schema = [  ################################## ADD MORE COLUMNS
            bigquery.SchemaField("match_id", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("request_data", "STRING"),
            bigquery.SchemaField("volunteer_data", "STRING"),
            bigquery.SchemaField("distance", "FLOAT"),
            bigquery.SchemaField("matched_timestamp", "TIMESTAMP"),
            bigquery.SchemaField("insertion_timestamp", "TIMESTAMP")
        ]

        tables_config = [
            ("unmatched_requests", requests_schema),
            ("unmatched_volunteers", volunteers_schema),
            ("matched_pairs", matched_pairs_schema)
        ]

        for table_name, schema in tables_config:
            self.create_table_if_not_exists(table_name, schema)

    def create_table_if_not_exists(self, table_name, schema):
        """Crea una tabla específica si no existe."""
        table_id = f"{self.dataset_ref}.{table_name}"
        try:
            table = bigquery.Table(table_id, schema=schema)
            
            # Usar matched_timestamp para matched_pairs y insertion_timestamp para las demás
            partition_field = "matched_timestamp" if table_name == "matched_pairs" else "insertion_timestamp"
            
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field=partition_field
            )
            self.client.create_table(table, exists_ok=True)
            logging.info(f"Tabla {table_name} está lista")
        except Exception as e:
            logging.error(f"Error creando tabla {table_name}: {e}")
            raise

class StoreBigQueryMatchedUsers(beam.DoFn):
    def __init__(self, project_id, dataset_id):
        self.project_id = project_id
        self.dataset_id = dataset_id
        
    def setup(self):
        self.client = bigquery.Client(project=self.project_id)
        self.processed_pairs = set()
        
    def process(self, element):
        category, matched_data = element
        
        try:
            # Crear una clave única para este par
            pair_key = f"{matched_data['request']['id']}_{matched_data['volunteer']['id']}"
            
            # Si ya procesamos este par, lo saltamos
            if pair_key in self.processed_pairs:
                return
            
            self.processed_pairs.add(pair_key)
            
            current_timestamp = datetime.now().isoformat()
            flattened_data = { ################################## ADD MORE COLUMNS
                "match_id": str(uuid.uuid4()),
                'category': category,
                'request_data': json.dumps(matched_data["request"]),
                'volunteer_data': json.dumps(matched_data["volunteer"]),
                'distance': matched_data.get("distance"),
                'matched_timestamp': current_timestamp,
                'insertion_timestamp': current_timestamp
            }
            
            errors = self.client.insert_rows_json(
                f"{self.project_id}.{self.dataset_id}.matched_pairs",
                [flattened_data]
            )
            if errors:
                logging.error(f"Error inserting matched rows: {errors}")
            
        except Exception as err:
            logging.error(f"Error storing matched user: {err}")

# class StoreBigQueryNotMatched(beam.DoFn):
#     def __init__(self, project_id, dataset_id):
#         self.project_id = project_id
#         self.dataset_id = dataset_id
        
#     def setup(self):
#         self.client = bigquery.Client(project=self.project_id)
        
#     def process(self, element):
#         events = ['request', 'volunteer']
#         category, (help_data, volunteer_data) = element
        
#         tables = {
#             'request': f"{self.project_id}.{self.dataset_id}.unmatched_requests",
#             'volunteer': f"{self.project_id}.{self.dataset_id}.unmatched_volunteers"
#         }
        
#         for event in events:
#             data_list = volunteer_data if event == 'volunteer' else help_data
#             if data_list:
#                 for record in data_list:
#                     try:
#                         record['categoria'] = category
#                         record['insertion_timestamp'] = datetime.now().isoformat()
#                         # Convertir created_at a timestamp si existe
#                         if 'created_at' in record:
#                             record['created_at'] = datetime.fromisoformat(record['created_at']).isoformat()
                        
#                         errors = self.client.insert_rows_json(
#                             tables[event],
#                             [record]
#                         )
#                         if errors:
#                             logging.error(f"Error inserting rows: {errors}")
#                     except Exception as err:
#                         logging.error(f"Error storing {event}: {err}")


def run():
    parser = argparse.ArgumentParser(description=('Input arguments for the Dataflow Streaming Pipeline.'))

    parser.add_argument(
                '--project_id',
                required=True,
                help='GCP cloud project name.')
    
    parser.add_argument(
                '--help_topic',
                required=False,
                help='PubSub topicc used for writing help requests data.')

    parser.add_argument(
                '--help_subscription',
                required=True,
                help='PubSub subscription used for reading help requests data.')
    
    parser.add_argument(
                '--volunteers_topic',
                required=False,
                help='PubSub topicc used for writing volunteers requests data.')
    
    parser.add_argument(
                '--volunteers_subscription',
                required=True,
                help='PubSub subscription used for reading volunteers data.')
    
    parser.add_argument(
                '--bigquery_dataset',
                required=True,
                help='The BigQuery dataset where matched users will be stored.')
    
    parser.add_argument(
                '--output_topic',
                required=False,
                help='PubSub Topic for matched users.')
    
    args, pipeline_opts = parser.parse_known_args()


# BigQuery configuration
    bq_setup = BigQuerySetup(args.project_id, args.bigquery_dataset)
    bq_setup.create_dataset_if_not_exists()
    bq_setup.create_tables_if_not_exist()


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
        
        # Partiton 2: New partition to separate requests and volunteers
        resend_request, resend_volunteer = (
            category_not_grouped | "Partition help and volunteer" >> beam.Partition(lambda kv, _: 0 if len(kv[1][0]) > 0 else 1, 2)
        )

        # Encode and send each partition to the corresponding PubSub topic
        (
            resend_request 
            | "Record attempts to match request" >> beam.ParDo(AddAttempts())
            | "Convert request to bytes" >> beam.Map(ConvertToBytes)
            | "Write to PubSub topic ayudantes-events" >> WriteToPubSub(topic=args.volunteers_topic, with_attributes=False)
        )
        (
            resend_volunteer 
            | "Record attempts to match volunteer" >> beam.ParDo(AddAttempts())
            | "Convert help to bytes" >> beam.Map(ConvertToBytes)
            | "Write to PubSub topic necesitados-events" >> WriteToPubSub(topic=args.help_topic, with_attributes=False)
        )

        # resend_request | "debug" >> beam.Map(lambda x: logging.info(f"Sent to pubsub topic ayudantes-events {x}"))
        # resend_volunteer | "debug 2" >> beam.Map(lambda x: logging.info(f"Sent to pubsub topic necesitados-events {x}"))

        # Partition 1: continues the Pipeline = Match by distance & Tagged Output
        filtered_data = ( 
            category_grouped
            | "Filter by distance" >> beam.ParDo(FilterbyDistance()).with_outputs("matched_users", "not_matched_users")
        )
        
        # # Store matched users to BigQuery
        # bq_matched = (
        #     filtered_data.matched_users
        #     | "Write matched_users to BigQuery" >> beam.ParDo(
        #         StoreBigQueryMatchedUsers(
        #             project_id=args.project_id,
        #             dataset_id=args.bigquery_dataset
        #         )
        #     )
        # )
        
        # Public to output topic
        # output_data = (
        #     filtered_data.matched_users
        #     | "Write to PubSub topic Output" >> beam.io.WriteToPubSub(topic=args.output_topic)
        # )
        
        # Separate data to store in Firestore and enable reprocessing
        # reprocess_data = (
        #     filtered_data.not_matched_users
        #         | "Remove distance" >> beam.Map(RemoveDistance)
        #         | "Separate help and volunteer" >> beam.FlatMap(lambda z: [
        #         (z[0], ([z[1].get('request', {})], [])),
        #         (z[0], ([], [z[1].get('volunteer', {})]))
        #     ])
        #     | "Store in BigQuery to reprocess" >> beam.ParDo(
        #         StoreBigQueryNotMatched(
        #             project_id=args.project_id,
        #             dataset_id=args.dataset_id
        #         )
        #     )
        # )



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("The process started")

    run()