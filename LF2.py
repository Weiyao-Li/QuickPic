import json
import os
import boto3
import time
import logging
import re
import datetime
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import inflection
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

region = "us-east-1"
host = "search-photos-eumyc7ppo2p53eh3lnadp7jyqq.us-east-1.es.amazonaws.com"
index = "photos"

lexv2 = boto3.client("lexv2-runtime")
def lambda_handler(event, context):

    msg_from_user = 'I need some photos with trees'
    response = lexv2.recognize_text(
        botId='5GMXHBNSCD',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='testuser',
        text=msg_from_user
    )

    keywords = []
    if 'interpretations' in response and len(response['interpretations']) > 0:
        interpretation = response['interpretations'][0]
        if 'slots' in interpretation["intent"]:
            for key, value in interpretation["intent"]["slots"].items():
                if key in ["query_term1", "query_term2"] and value:
                    key_words = value["value"]["interpretedValue"]
                    if " " in key_words:
                        key_words = key_words.split(" ")
                        for word in key_words:
                            keywords.append(inflection.inflection.singularize(word))
                    else:
                        keywords.append(inflection.inflection.singularize(key_words))
    # lex delete query3
    print(keywords)
    if keywords:
        img_paths = search_photos(keywords)

    if not img_paths:
        return {
            'statusCode': 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            'body': json.dumps('No Results found')
        }
    else:
        return {
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin": "*"},
            'body': {
                'imagePaths': img_paths,
                'userQuery': q1,
                'labels': labels,
            }
        }


def search_photos(keywords):
    query = {
        "query": {
            "bool": {
                "should": []
            }
        }
    }

    for key in keywords:
        query['query']['bool']['should'].append({
            "match": {
                "labels": key
            }
        })

    opensearch = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=get_awsauth(region, "es"),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    try:
        response = opensearch.search(body=query, index="photos")
        print(response)
        hits = response['hits']['hits']
        return hits

    except Exception as e:
        print(f"Error while searching OpenSearch index: {str(e)}")
        return []

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
