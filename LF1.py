import boto3
import json
import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests aws4auth import AWS4Auth

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

REGION = 'us-east-1'
HOST = 'search-photos-eumyc7ppo2p53eh3lnadp7jyqq.us-east-1.es.amazonaws.com'
INDEX = 'photos'

opensearch = boto3.client('es', endpoint_url=f'https://{HOST}')

def lambda_handler(event, context):
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']

    try:
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        labels = [label['Name'] for label in response['Labels']]
        print('Labels:', labels)

        metadata = s3.head_object(Bucket=bucket, Key=key)['Metadata']
        custom_labels = metadata.get('x-amz-meta-customLabels')
        if custom_labels:
            custom_labels = json.loads(custom_labels)
            labels.extend(custom_labels)

        object_metadata = s3.head_object(Bucket=bucket, Key=key)['Metadata']
        created_timestamp = object_metadata.get('creation-date')
        if created_timestamp:
            created_timestamp = datetime.datetime.strptime(created_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').isoformat()

        json_data = {
            'objectKey': key,
            'bucket': bucket,
            'createdTimestamp': created_timestamp,
            'labels': labels
        }
        print('JSON data:', json_data)

        opensearch.index(
            index=INDEX,
            body=json_data
        )

    except Exception as e:
        print(e)
        raise e
