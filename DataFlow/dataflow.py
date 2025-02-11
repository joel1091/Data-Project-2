import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from apache_beam.metrics import Metrics
from google.cloud import bigquery

from datetime import datetime
import argparse
import logging
import json
import math

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
        matched_pairs_schema = [
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("request_id", "STRING"),
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

def parse_pubsub_message(message):
    """Función unificada para parsear mensajes de PubSub"""
    try:
        pubsub_message = message.decode('utf-8')
        msg = json.loads(pubsub_message)
        return msg['categoria'], msg
    except Exception as e:
        logging.error(f"Error parsing message: {e}")
        logging.error(f"Message content: {message}")
        raise

def remove_distance(data_list):
    """Elimina el campo distance de los registros"""
    if isinstance(data_list, dict):
        if 'distance' in data_list:
            del data_list['distance']
        return data_list
    for record in data_list:
        if 'distance' in record:
            del record['distance']
    return data_list

class StoreBigQueryNotMatched(beam.DoFn):
    def __init__(self, project_id, dataset_id):
        self.project_id = project_id
        self.dataset_id = dataset_id
        
    def setup(self):
        self.client = bigquery.Client(project=self.project_id)
        
    def process(self, element):
        events = ['request', 'volunteer']
        category, (help_data, volunteer_data) = element
        
        tables = {
            'request': f"{self.project_id}.{self.dataset_id}.unmatched_requests",
            'volunteer': f"{self.project_id}.{self.dataset_id}.unmatched_volunteers"
        }
        
        for event in events:
            data_list = volunteer_data if event == 'volunteer' else help_data
            if data_list:
                for record in data_list:
                    try:
                        record['categoria'] = category
                        record['insertion_timestamp'] = datetime.now().isoformat()
                        # Convertir created_at a timestamp si existe
                        if 'created_at' in record:
                            record['created_at'] = datetime.fromisoformat(record['created_at']).isoformat()
                        
                        errors = self.client.insert_rows_json(
                            tables[event],
                            [record]
                        )
                        if errors:
                            logging.error(f"Error inserting rows: {errors}")
                    except Exception as err:
                        logging.error(f"Error storing {event}: {err}")

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
            flattened_data = {
                'category': category,
                'request_id': matched_data["request"].get("id"),
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
                
            # Una vez matcheado, removemos el request y volunteer de sus respectivas tablas
            self.remove_matched_entries(matched_data)
            
        except Exception as err:
            logging.error(f"Error storing matched user: {err}")
            
    def remove_matched_entries(self, matched_data):
        try:
            # Eliminar de unmatched_requests
            request_query = f"""
            DELETE FROM `{self.project_id}.{self.dataset_id}.unmatched_requests`
            WHERE id = '{matched_data['request']['id']}'
            """
            
            # Eliminar de unmatched_volunteers
            volunteer_query = f"""
            DELETE FROM `{self.project_id}.{self.dataset_id}.unmatched_volunteers`
            WHERE id = '{matched_data['volunteer']['id']}'
            """
            
            self.client.query(request_query).result()
            self.client.query(volunteer_query).result()
            
        except Exception as e:
            logging.error(f"Error removing matched entries: {e}")

class FilterbyDistance(beam.DoFn):
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radio de la Tierra en kilómetros
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def process(self, element):
        category, (help_data, volunteer_data) = element
        
        if not help_data or not volunteer_data:
            return

        for volunteer in volunteer_data:
            try:
                lat_volunteer, lon_volunteer = map(float, volunteer['ubicacion'].split(','))
                radio_max = float(volunteer.get('radio_disponible_km', 100))

                for request in help_data:
                    try:
                        lat_request, lon_request = map(float, request['ubicacion'].split(','))
                        distance = self.haversine(lat_volunteer, lon_volunteer, lat_request, lon_request)
                        
                        data = (category, {
                            "request": request,
                            "volunteer": volunteer,
                            "distance": distance
                        })
                        
                        if distance <= radio_max:
                            yield data
                            yield beam.pvalue.TaggedOutput("matched_users", data)
                        else:
                            yield beam.pvalue.TaggedOutput("not_matched_users", data)
                    except ValueError as e:
                        logging.error(f"Error processing request location: {e}")
                        continue
            except ValueError as e:
                logging.error(f"Error processing volunteer location: {e}")
                continue

def run():
    parser = argparse.ArgumentParser(description='Input arguments for the Dataflow Streaming Pipeline.')
    
    parser.add_argument(
        '--project_id',
        required=True,
        help='GCP cloud project name.'
    )
    
    parser.add_argument(
        '--help_subscription',
        required=True,
        help='PubSub subscription used for reading help requests data.'
    )
    
    parser.add_argument(
        '--volunteers_subscription',
        required=True,
        help='PubSub subscription used for reading volunteers data.'
    )
    
    parser.add_argument(
        '--dataset_id',
        required=True,
        help='The BigQuery dataset where data will be stored.'
    )

    args, pipeline_opts = parser.parse_known_args()

    # Configurar BigQuery antes de iniciar el pipeline
    bq_setup = BigQuerySetup(args.project_id, args.dataset_id)
    bq_setup.create_dataset_if_not_exists()
    bq_setup.create_tables_if_not_exist()

    # Pipeline Options
    options = PipelineOptions(
        pipeline_opts,
        save_main_session=True,
        streaming=True,
        project=args.project_id
    )
    
    # Pipeline Object
    with beam.Pipeline(options=options) as p:
        help_data = (
            p
            | "Read help data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.help_subscription)
            | "Parse JSON help messages" >> beam.Map(parse_pubsub_message)
            | "Fixed Window for help data" >> beam.WindowInto(window.FixedWindows(30))  # Ventana fija de 30 segundos
        )

        volunteer_data = (
            p
            | "Read volunteer data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.volunteers_subscription)
            | "Parse JSON volunteer messages" >> beam.Map(parse_pubsub_message)
            | "Fixed Window for volunteer data" >> beam.WindowInto(window.FixedWindows(30))  # Ventana fija de 30 segundos
        )

        # CoGroupByKey
        grouped_data = (help_data, volunteer_data) | "Merge PCollections" >> beam.CoGroupByKey()

        # Partitions
        category_grouped, category_not_grouped = (
            grouped_data 
            | "Partition by volunteer found" >> beam.Partition(
                lambda kv, _: 0 if len(kv[1][0]) and len(kv[1][1]) > 0 else 1, 
                2
            )
        )
        
        # Store not grouped in BigQuery
        _ = (
            category_not_grouped
            | "Send not grouped messages to BigQuery" >> beam.ParDo(
                StoreBigQueryNotMatched(
                    project_id=args.project_id,
                    dataset_id=args.dataset_id
                )#-------------------------------------------------------------------AQUI HABRIA QUE PONER EL FILTRO DE QUE SI LA VARIABLE INTENTO NO ES > 3 QUE NO SE HAGA (o abajo cuando se use)
            )
        )

        # Filter by distance & Tagged Output
        filtered_data = (
            category_grouped
            | "Filter by distance" >> beam.ParDo(FilterbyDistance()).with_outputs(
                "matched_users",
                "not_matched_users"
            )
        )
        
        # Store matched users to BigQuery
        _ = (
            filtered_data.matched_users
            | "Write matched_users to BigQuery" >> beam.ParDo(
                StoreBigQueryMatchedUsers(
                    project_id=args.project_id,
                    dataset_id=args.dataset_id
                )
            )
        )
        
        # Reprocess unmatched by distance
        _ = (
            filtered_data.not_matched_users
            | "Remove distance" >> beam.Map(remove_distance)
            | "Separate help and volunteer" >> beam.FlatMap(lambda z: [
                (z[0], ([z[1].get('request', {})], [])),
                (z[0], ([], [z[1].get('volunteer', {})]))
            ])
            | "Store in BigQuery to reprocess" >> beam.ParDo(
                StoreBigQueryNotMatched(
                    project_id=args.project_id,
                    dataset_id=args.dataset_id
                )
            )
        )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("The process started")
    run()