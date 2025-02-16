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
    help_data = data["help"]
    volunteer_data = data["volunteer"]

    return {
        "match_id": str(uuid.uuid4()), 
        "categoria": categoria,
        "distance": data["distance"],
        #Help fields
        "urgencia": help_data["nivel_urgencia"],
        "help_nombre": help_data["nombre"],
        "help_ubicacion": help_data["ubicacion"],
        "help_poblacion": help_data["poblacion"],
        "help_descripcion": help_data["descripcion"],
        "help_telefono": help_data["telefono"],
        "help_created_at": help_data["created_at"],
        #Volunteer fields
        "volunteer_nombre": volunteer_data["nombre"],
        "volunteer_ubicacion": volunteer_data["ubicacion"],
        "volunteer_poblacion": volunteer_data["poblacion"],
        "volunteer_radio_disponible_km": volunteer_data["radio_disponible_km"],  
        "volunteer_created_at": volunteer_data["created_at"]
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
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c  
    
    def process(self, element):
        category, (help_data, volunteer_data) = element
        
        # We initialize the sets to track the IDs
        matched_helps = set()
        matched_volunteers = set()
        
        if len(help_data) and len(volunteer_data) > 0:
            # We convert help_data and volunteer_data to lists to modify them
            available_volunteers = list(volunteer_data)
            
            # We order help_data by level_urgency (from highest to lowest)
            sorted_help_data = sorted(help_data, key=lambda x: x.get('nivel_urgencia', 0), reverse=True)
            
            for help in sorted_help_data:
                if not available_volunteers:  
                    if help['id'] not in matched_helps:
                        yield beam.pvalue.TaggedOutput("not_matched_users", help)
                        logging.info(f"No more volunteers available for Help ID: {help['id']}")
                    continue
                    
                found_match = False
                lat_request, lon_request = map(float, help['ubicacion'].split(','))
                
                # Find the closest volunteer on the radio
                closest_volunteer = None
                min_distance = float('inf')
                volunteer_index = -1
                
                for i, volunteer in enumerate(available_volunteers):
                    lat_volunteer, lon_volunteer = map(float, volunteer['ubicacion'].split(','))
                    radio_max = volunteer.get('radio_disponible_km')
                    
                    distance = self.haversine(lat_volunteer, lon_volunteer, lat_request, lon_request)
                    
                    if distance <= radio_max and distance < min_distance:
                        min_distance = distance
                        closest_volunteer = volunteer
                        volunteer_index = i
                
                if closest_volunteer:
                    data = (category, {
                        "help": help,
                        "volunteer": closest_volunteer,
                        "distance": min_distance
                    })
                    yield beam.pvalue.TaggedOutput("matched_users", data)
                    matched_helps.add(help['id'])
                    matched_volunteers.add(closest_volunteer['id'])
                    found_match = True
                    logging.info(f"Match found - Help ID: {help['id']}, Urgency: {help.get('nivel_urgencia', 0)}, Volunteer ID: {closest_volunteer['id']}, Distance: {min_distance}")
                    
                    # Remove used volunteer from available list
                    available_volunteers.pop(volunteer_index)
                
                if not found_match and help['id'] not in matched_helps:
                    yield beam.pvalue.TaggedOutput("not_matched_users", help)
                    logging.info(f"No match found for Help ID: {help['id']}")
            
            # Issue volunteers who did not match
            for volunteer in available_volunteers:
                if volunteer['id'] not in matched_volunteers:
                    yield beam.pvalue.TaggedOutput("not_matched_users", volunteer)
                    logging.info(f"No match found for Volunteer ID: {volunteer['id']}")
        
        else:
            # Case where one of the groups is empty 
            if len(help_data) > 0:
                for help_item in help_data:
                    yield beam.pvalue.TaggedOutput("not_matched_users", help_item)
                    logging.info(f"No volunteers available for Help ID: {help_item['id']}")
            elif len(volunteer_data) > 0:
                for volunteer_item in volunteer_data:
                    yield beam.pvalue.TaggedOutput("not_matched_users", volunteer_item)
                    logging.info(f"No help requests available for Volunteer ID: {volunteer_item['id']}")

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
                {"name": "distance", "type": "FLOAT", "mode": "NULLABLE"},
                # Help fields
                {"name": "urgencia", "type": "INTEGER", "mode": "NULLABLE"},
                {"name": "help_nombre", "type": "STRING", "mode": "NULLABLE"},
                {"name": "help_ubicacion", "type": "STRING", "mode": "NULLABLE"},
                {"name": "help_poblacion", "type": "STRING", "mode": "NULLABLE"},
                {"name": "help_descripcion", "type": "STRING", "mode": "NULLABLE"},
                {"name": "help_telefono", "type": "STRING", "mode": "NULLABLE"},
                {"name": "help_created_at", "type": "TIMESTAMP", "mode": "NULLABLE"},
                # Volunteer fields
                {"name": "volunteer_nombre", "type": "STRING", "mode": "NULLABLE"},
                {"name": "volunteer_ubicacion", "type": "STRING", "mode": "NULLABLE"},
                {"name": "volunteer_poblacion", "type": "STRING", "mode": "NULLABLE"},
                {"name": "volunteer_radio_disponible_km", "type": "INTEGER", "mode": "NULLABLE"},
                {"name": "volunteer_created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
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