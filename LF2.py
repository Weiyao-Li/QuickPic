import os
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.helpers import to_dict
from botocore.exceptions import ClientError
from requests_aws4auth import AWS4Auth

REGION = "us-east-1"
LEX_RUNTIME = boto3.client('lexv2-runtime', region_name=REGION)
OPENSEARCH_ENDPOINT = "search-photos-eumyc7ppo2p53eh3lnadp7jyqq.us-east-1.es.amazonaws.com"
OPENSEARCH_INDEX = "photos"

lexv2 = boto3.client("lexv2-runtime")
# Set up OpenSearch client
def get_awsauth(REGION, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    REGION,
                    service,
                    session_token=cred.token)



def lambda_handler(event, context):
    query = event["queryString"]



    # Disambiguate the query using Amazon Lex V2 bot

    response = lexv2.recognize_text(
        botId='5GMXHBNSCD',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='testuser',
        text=query
    )
    print(response)
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
    if len(keywords)>1:
        term = " ".join(keywords)
        q = {'size': 20, 'query': {'multi_match': {'query': term}}}
    else:
        q =  {'size': 20, 'query': {'multi_match': {'query': keywords[0]}}}

    try:
        opensearch = OpenSearch(
            hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
            http_auth=get_awsauth(REGION, "es"),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        response = opensearch.search(index=OPENSEARCH_INDEX, body=q)
    except Exception as e:
        print(f"Error while searching OpenSearch index: {str(e)}")
        return []

    results = [to_dict(hit["_source"]) for hit in response["hits"]["hits"]]
    return results

