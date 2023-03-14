import json
import boto3
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

REGION = 'us-east-1'
HOST = 'search-photos-eumyc7ppo2p53eh3lnadp7jyqq.us-east-1.es.amazonaws.com'

def lambda_handler(event, context):
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']

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

    now = datetime.datetime.now()
    created_timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")

    json_data = {
        'objectKey': key,
        'bucket': bucket,
        'createdTimestamp': created_timestamp,
        'labels': labels
    }
    print('JSON data:', json_data)

    es_payload = json.dumps(json_data).encode("utf-8")

    client_OpenSearch = OpenSearch(
        hosts=[{'host': HOST, 'port': 443, 'scheme': 'https'}],
        http_auth=get_awsauth(REGION, 'es'),
        use_ss1=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    try:
        response_from_opensearch = client_OpenSearch.index(
            index='photos',
            body=es_payload)
        print("successful")

    except Exception as e:
        logger.error(str(e))
        print("failed insertion")


def get_awsauth(REGION, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    REGION,
                    service,
                    session_token=cred.token)
