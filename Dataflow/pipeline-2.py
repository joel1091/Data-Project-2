import apache_beam as beam
from apache_beam.runners import DataflowRunner
from apache_beam.options.pipeline_options import PipelineOptions
import apache_beam.transforms.window as window
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

# class AddAttempts(beam.DoFn):
def AddAttempts(element):
    item = element
    if "attempts" not in item:
        item["attempts"] = 0
    item["attempts"] += 1
    return item

        # if item["attempts"] >= 5:
        #     yield beam.pvalue.TaggedOutput("max_attempts", element)

        # else:
        #     yield beam.pvalue.TaggedOutput("valid", element)


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

        if len(element[1][0]) and len(element[1][1]) > 0:

            for volunteer in volunteer_data:
                lat_volunteer, lon_volunteer = map(float, volunteer['ubicacion'].split(','))
                radio_max = volunteer.get('radio_disponible_km')

            for help in help_data:
                lat_request, lon_request = map(float, help['ubicacion'].split(','))
                distance = self.haversine(lat_volunteer, lon_volunteer, lat_request, lon_request)
                
                data = (category, {"help": help,
                                    "volunteer": volunteer,
                                    "distance": distance
                                    })
                
                if distance <= radio_max:
                    yield beam.pvalue.TaggedOutput("matched_users", data)
                    logging.info(f"Match found: {data}")  
                else:
                    help_data = data[1].get('help')
                    yield beam.pvalue.TaggedOutput("not_matched_users", help_data)
                    volunteer_data = data[1].get('volunteer')                   
                    yield beam.pvalue.TaggedOutput("not_matched_users", volunteer_data)
                    # logging.info(f"HELP: {help_data}")  
                    # logging.info(f"VOLUNTEER:{volunteer_data}")
        else:
            if len(element[1][0]) > 0:
                help_data = element[1][0][0]
                yield beam.pvalue.TaggedOutput("not_matched_users", help_data)
                # logging.info(f"HELP - SECOND LEVEL: {help_data}")  
            elif len(element[1][1]) > 0:
                volunteer_data = element[1][1][0]
                yield beam.pvalue.TaggedOutput("not_matched_users", volunteer_data)
                # logging.info(f"VOLUNTEER - SECOND LEVEL: {volunteer_data}")


class PrepareForPubSub(beam.DoFn):
    def ConvertToBytes(element):
        data = element
        message_bytes = json.dumps(data).encode('utf-8')
        return message_bytes

    def process(self,element):
        data = element
        if data["nivel_urgencia"]:
            self.ConvertToBytes()
            yield beam.pvalue.TaggedOutput("help", data)
        if data["radio_disponible_km"]:
            self.ConvertToBytes()
            yield beam.pvalue.TaggedOutput("volunteer", data)            


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
                required=False,
                help='The BigQuery dataset where matched users will be stored.')
    
    parser.add_argument(
                '--output_topic',
                required=False,
                help='PubSub Topic for matched users.')
    
    args, pipeline_opts = parser.parse_known_args()


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
        grouped_data = ( 
            (help_data,volunteer_data)
            | "Merge PCollections" >> beam.CoGroupByKey()
            | "Match by Distance" >> beam.ParDo(FilterbyDistance()).with_outputs("matched_users", "not_matched_users")
        )

    #     grouped_data.matched_users | "Write matches to BigQuery" >> beam.io.WriteToBigQuery(
    #     table=f"{args.project_id}:{args.bigquery_dataset}.matched_pairs",
    #     schema = {     "fields": [         
    #         {"name": "categoria",  "type": "STRING", "mode": "NULLABLE"},         
    #         {"name": "help",       "type": "STRING", "mode": "NULLABLE"},         
    #         {"name": "volunteer",  "type": "STRING", "mode": "NULLABLE"},         
    #         {"name": "distance", "type": "FLOAT", "mode": "NULLABLE"} ] },
    #     write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
    #     create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
    # )

        with_attempts = (
            grouped_data.not_matched_users| "Add attempt" >> beam.Map(AddAttempts)
        )
        
        max_attempts_data, valid_data = (
        with_attempts
        | "Partitions Max / Valid" >> beam.Partition(
        lambda element, _: 0 if element["attempts"] >= 5 else 1, 2 
    ))

        (
            max_attempts_data
            | "encode para eliminar" >> beam.Map(lambda x: json.dumps(x).encode('utf-8'))
            | "send to deadletter" >> WriteToPubSub(topic="projects/total-glider-447114-u4/topics/output-topic", with_attributes=False)
         )
        # count_attempt.max_attempts | "Write to Big Query not matched" >> beam.io.WriteToBigQuery()

        max_attempts_data | "Logs attempts" >> beam.Map(lambda x: logging.info(f"Máximo alcanzado: {x}"))
        

        help_volunteer = (
            valid_data
            | "Differentiate and Convert to bytes" >> beam.ParDo(PrepareForPubSub()).with_outputs("help", "volunteer")
            )
        

        help_volunteer.help | "Resend help to PubSub" >> WriteToPubSub(topic=args.help_topic, with_attributes=False)

        help_volunteer.volunteer | "Resend volunteer to PubSub" >> WriteToPubSub(topic=args.volunteers_topic, with_attributes=False)
        


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("apache_beam.utils.subprocess_server").setLevel(logging.ERROR)
    logging.info("The process started")

    run()
        






