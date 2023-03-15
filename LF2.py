import os
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import to_dict
from botocore.exceptions import ClientError
from requests_aws4auth import AWS4Auth

REGION = os.environ['AWS_REGION']
LEX_RUNTIME = boto3.client('lexv2-runtime', region_name=REGION)
OPENSEARCH_ENDPOINT = os.environ['OPENSEARCH_ENDPOINT']
OPENSEARCH_INDEX = "photos"

# Set up AWS authentication for OpenSearch
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, 'es', session_token=credentials.token)

# Set up OpenSearch client
opensearch = OpenSearch(
    hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

def lambda_handler(event, context):
    query = event["queryString"]

    # Disambiguate the query using Amazon Lex V2 bot
    try:
        response = LEX_RUNTIME.recognize_text(
            botId='YourBotId',
            botAliasId='YourBotAliasId',
            localeId='en_US', # Replace this with your bot's locale
            sessionId='YourSessionId',
            text=query
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
        return {"results": []}

    # If Amazon Lex V2 disambiguation request yields any keywords
    keywords = []
    if 'interpretations' in response and len(response['interpretations']) > 0:
        interpretation = response['interpretations'][0]
        if 'slots' in interpretation:
            for slot in interpretation['slots']:
                if slot['value']['interpretedValue']:
                    keywords.append(slot['value']['interpretedValue'])

    # Search the OpenSearch index for results and return them accordingly
    if keywords:
        search_results = search_photos(keywords)
        return {"results": search_results}
    else:
        return {"results": []}

def search_photos(keywords):
    query_body = {
        "query": {
            "bool": {
                "should": [{"match": {"description": keyword}} for keyword in keywords]
            }
        }
    }

    try:
        response = opensearch.search(index=OPENSEARCH_INDEX, body=query_body)
    except Exception as e:
        print(f"Error while searching OpenSearch index: {str(e)}")
        return []

    results = [to_dict(hit["_source"]) for hit in response["hits"]["hits"]]
    return results
