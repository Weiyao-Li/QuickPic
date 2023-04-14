import json
import boto3
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import datetime
import logging
import base64

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

s3 = boto3.client('s3')
REGION = 'us-east-1'
rekognition = boto3.client('rekognition', region_name=REGION)

HOST = 'search-photoscf-dzv7stkzlfny5xr77e4f357dte.us-east-1.es.amazonaws.com'


def lambda_handler(event, context):
    print("hello world")
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']

    metadata = s3.head_object(Bucket=bucket, Key=key)['Metadata']
    custom_labels = metadata.get('customlabels')
    print(custom_labels)

    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode("utf-8")

    image = base64.b64decode(content)

    # delete original photos and upload new one in s3
    response = s3.delete_object(Bucket=bucket, Key=key)
    response = s3.put_object(Bucket=bucket, Body=image, Key=key, ContentType='image/jpg')

    response = rekognition.detect_labels(
        Image={'Bytes': image}
    )
    labels = [label['Name'] for label in response['Labels']]
    print('Labels:', labels)

    if custom_labels:
        labels.append(custom_labels)

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
            index='photoscf',
            body=es_payload)

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