import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
from google.cloud import bigquery
from apache_beam.io import WriteToPubSub
from apache_beam.transforms.trigger import AccumulationMode

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

# Indicate schema/value
def FormatBigQueryMatched(element):
    categoria, data = element
    return {
        "match_id": str(uuid.uuid4()), 
        "categoria": categoria,
        "help": json.dumps(data["help"]),
        "volunteer": json.dumps(data["volunteer"]),
        "distance": data["distance"]
    }

# Add attempts to unmatched messages
def AddAttempts(element):
    if "attempts" not in element:
        element["attempts"] = 0
    element["attempts"] += 1
    return element


def partition_by_attempts(element, num_partitions):
            current_attempts = element.get('attempts', 0)
            if current_attempts >= 5:
                return 1 
            return 0 

# Filter by distance
class FilterbyDistance(beam.DoFn):
    @staticmethod
    # Calculate distance based on coordinates
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c  
    
    # Filter by distance according to "radio_disponible_km" & tag not_matched_users and matched_users
    def process(self, element):
        category, (help_data, volunteer_data) = element

        if len(element[1][0]) and len(element[1][1]) > 0:
            for help in help_data:
                lat_request, lon_request = map(float, help['ubicacion'].split(','))

                for volunteer in volunteer_data:
                    lat_volunteer, lon_volunteer = map(float, volunteer['ubicacion'].split(','))
                    radio_max = volunteer.get('radio_disponible_km')

                    distance = self.haversine(lat_volunteer, lon_volunteer, lat_request, lon_request)

                    data = (category, {"help": help, 
                                    "volunteer": volunteer, 
                                    "distance": distance})

                    if distance <= radio_max:
                        yield beam.pvalue.TaggedOutput("matched_users", data)
                        logging.info(f"Match found: {data}")
                    else:
                        yield beam.pvalue.TaggedOutput("not_matched_users", help)
                        logging.info(f"HELP - FIRST LEVEL: {help}")
                        yield beam.pvalue.TaggedOutput("not_matched_users", volunteer) 
                        logging.info(f"VOLUNTEER - FIRST LEVEL: {volunteer}")

        else:
            if len(element[1][0]) > 0:
                for help_item in help_data:
                    yield beam.pvalue.TaggedOutput("not_matched_users", help_item) 
                    logging.info(f"HELP - SECOND LEVEL: {help_item}")
            elif len(element[1][1]) > 0:
                for volunteer_item in volunteer_data:
                    yield beam.pvalue.TaggedOutput("not_matched_users", volunteer_item)
                    logging.info(f"VOLUNTEER - SECOND LEVEL: {volunteer_item}")


class PrepareForPubSub(beam.DoFn):
    @staticmethod
    def ConvertToBytes(element):
        message_bytes = json.dumps(element).encode('utf-8')
        return message_bytes

    def process(self,element):
        if element.get("nivel_urgencia"):
            yield beam.pvalue.TaggedOutput("help", self.ConvertToBytes(element))
        if element.get("radio_disponible_km"):
            yield beam.pvalue.TaggedOutput("volunteer", self.ConvertToBytes(element))            

# Store not matched in BigQuery after 5 attempts
class StoreBigQueryNotMatched(beam.DoFn):
    def FormatBigQueryHelp(self, element):
        return {
            "id": element["id"],
            "nombre": element["nombre"],
            "ubicacion": element["ubicacion"],
            "poblacion": element["poblacion"],
            "categoria": element["categoria"],
            "descripcion": element["descripcion"],
            "created_at": element["created_at"],
            "nivel_urgencia": element["nivel_urgencia"],
            "telefono": element["telefono"],
            "attempts": element["attempts"],
            "insertion_stamp": datetime.now().isoformat()
        }
    def FormatBigQueryVolunteer(self, element):
        return {
            "id": element["id"],
            "nombre": element["nombre"],
            "ubicacion": element["ubicacion"],
            "poblacion": element["poblacion"],
            "categoria": element["categoria"],
            "radio_disponible_km": element["radio_disponible_km"],
            "created_at": element["created_at"],
            "attempts": element["attempts"],
            "insertion_stamp": datetime.now().isoformat()
        }

    def process(self, element):
        if "nivel_urgencia" in element:
            yield beam.pvalue.TaggedOutput("unmatched_requests", self.FormatBigQueryHelp(element))
            logging.info(f"Sending to BQ - help: {element}")
        if "radio_disponible_km" in element:
            yield beam.pvalue.TaggedOutput("unmatched_volunteers", self.FormatBigQueryVolunteer(element))
            logging.info(f"Sending to BQ - volunteer: {element}")




def run():
    parser = argparse.ArgumentParser(description=('Input arguments for the Dataflow Streaming Pipeline.'))

    parser.add_argument(
                '--project_id',
                required=True,
                help='GCP cloud project name.')
    
    parser.add_argument(
                '--help_topic',
                required=True,
                help='PubSub topic used for writing help requests data.')

    parser.add_argument(
                '--help_subscription',
                required=True,
                help='PubSub subscription used for reading help requests data.')
    
    parser.add_argument(
                '--volunteers_topic',
                required=True,
                help='PubSub topic used for writing volunteers requests data.')
    
    parser.add_argument(
                '--volunteers_subscription',
                required=True,
                help='PubSub subscription used for reading volunteers data.')
    
    parser.add_argument(
                '--bigquery_dataset',
                required=True,
                help='The BigQuery dataset where matched users will be stored.')
    
    # parser.add_argument(
    #             '--output_topic',
    #             required=False,
    #             help='PubSub Topic for matched users.')
    
    args, pipeline_opts = parser.parse_known_args()


    # Pipeline Options
    options = PipelineOptions(pipeline_opts,
            save_main_session=True, streaming=True, project=args.project_id)
    
    # Pipeline Object
    with beam.Pipeline(argv=pipeline_opts,options=options) as p:
        # Read from PubSub & transformations to the correct format
        help_data = (
            p
                | "Read help data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.help_subscription)
                | "Parse JSON help messages" >> beam.Map(ParsePubSubMessage)
                | "Fixed Window for help data" >> beam.WindowInto(
                beam.window.FixedWindows(60),
                accumulation_mode=AccumulationMode.DISCARDING
            )
                | "Convert to tuple (categoria, id, data) for help" >> beam.Map(lambda kv: (kv[0], kv[1]['id'], kv[1]))  
                | "Remove duplicates by help id" >> beam.Distinct()  
                | "Restore key-value structure for help" >> beam.Map(lambda x: (x[0], x[2]))
        )

        volunteer_data = (
            p
                | "Read volunteer data from PubSub" >> beam.io.ReadFromPubSub(subscription=args.volunteers_subscription)
                | "Parse JSON volunteer messages" >> beam.Map(ParsePubSubMessage)
                | "Fixed Window for volunteer data" >> beam.WindowInto(
                beam.window.FixedWindows(60),
                accumulation_mode=AccumulationMode.DISCARDING
            )
                | "Convert to tuple (categoria, id, data) for volunteers" >> beam.Map(lambda kv: (kv[0], kv[1]['id'], kv[1]))  
                | "Remove duplicates by volunteer id" >> beam.Distinct()  
                | "Restore key-value structure for volunteers" >> beam.Map(lambda x: (x[0], x[2]))
        )

        # CoGroupByKey & Filter by Distance (depending on "radio_disponible_km" of the volunteer)
        grouped_data = ( 
            (help_data,volunteer_data)
            | "Merge PCollections" >> beam.CoGroupByKey()
            | "Match by Distance" >> beam.ParDo(FilterbyDistance()).with_outputs("matched_users", "not_matched_users")
        )

        # For tag matched_users, correct format to insert to BigQuery
        formated_matched_data = (
            grouped_data.matched_users
            | "Format matched data for BigQuery" >> beam.Map(FormatBigQueryMatched)
        )
        # Insert matches to BigQuery
        formated_matched_data | "Write matches to BigQuery" >> beam.io.WriteToBigQuery(
        table=f"{args.project_id}:{args.bigquery_dataset}.matched_pairs",
        schema = {
        "fields": [
            {"name": "match_id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria", "type": "STRING", "mode": "NULLABLE"},
            {"name": "help", "type": "STRING", "mode": "NULLABLE"},
            {"name": "volunteer", "type": "STRING", "mode": "NULLABLE"},
            {"name": "distance", "type": "FLOAT", "mode": "NULLABLE"}
        ]},
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
    )
        
        # For tag not_matched_users, add field "attempts"
        with_attempts = (
            grouped_data.not_matched_users| "Add attempt" >> beam.Map(AddAttempts)
        )
        
        # Messages with attempts, check if attempts > = 5. Separate in 2 partitions
        partitions = (
            with_attempts
            | "Partition data" >> beam.Partition(partition_by_attempts, 2)
        )
        valid_data = partitions[0]
        max_attempts_data = partitions[1]

        max_attempts_data | "Log max attempts partition" >> beam.Map(lambda x: logging.info(f"Maxed out: {x}"))


        # Partition 1 has reached max attempts and we send them to BigQuery
        send_BQ = (
            max_attempts_data | "Format help and volunteer messages for BQ" >> beam.ParDo(StoreBigQueryNotMatched()).with_outputs("unmatched_requests", "unmatched_volunteers")
        )

        # Write to BigQuery unmatched help 
        send_BQ.unmatched_requests | "Write to Big Query not matched help" >> beam.io.WriteToBigQuery(
        table=f"{args.project_id}:{args.bigquery_dataset}.unmatched_requests",
        schema = {
        "fields": [
            {"name": "id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nombre", "type": "STRING", "mode": "NULLABLE"},
            {"name": "ubicacion", "type": "STRING", "mode": "NULLABLE"},
            {"name": "poblacion", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria", "type": "STRING", "mode": "NULLABLE"},
            {"name": "descripcion", "type": "STRING", "mode": "NULLABLE"},
            {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
            {"name": "nivel_urgencia", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "telefono", "type": "STRING", "mode": "NULLABLE"},
            {"name": "insertion_stamp", "type": "TIMESTAMP", "mode": "NULLABLE"},
            {"name": "attempts", "type": "INTEGER", "mode": "NULLABLE"}
        ]},
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
        )

        # Write to BigQuery unmatched volunteers
        send_BQ.unmatched_volunteers | "Write to Big Query not matched volunteers" >> beam.io.WriteToBigQuery(
        table=f"{args.project_id}:{args.bigquery_dataset}.unmatched_volunteers",
        schema = {
        "fields": [
            {"name": "id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "nombre", "type": "STRING", "mode": "NULLABLE"},
            {"name": "ubicacion", "type": "STRING", "mode": "NULLABLE"},
            {"name": "poblacion", "type": "STRING", "mode": "NULLABLE"},
            {"name": "categoria", "type": "STRING", "mode": "NULLABLE"},
            {"name": "radio_disponible_km", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
            {"name": "attempts", "type": "INTEGER", "mode": "NULLABLE"},
            {"name": "insertion_stamp", "type": "TIMESTAMP", "mode": "NULLABLE"},
        ]},
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
        )
        
        # Partition 0: Messages with attempts < 5, clasify by help/volunteer and convert to bytes (for PubSub)
        help_volunteer = (
            valid_data
            | "Differentiate and Convert to bytes" >> beam.ParDo(PrepareForPubSub()).with_outputs("help", "volunteer")
            )
        
        # Resend valid messages to both topics: help and volunteers
        help_volunteer.help | "Resend help to PubSub" >> WriteToPubSub(topic=args.help_topic, with_attributes=False)
        help_volunteer.volunteer | "Resend volunteer to PubSub" >> WriteToPubSub(topic=args.volunteers_topic, with_attributes=False)
        


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("The process started")

    run()
        






