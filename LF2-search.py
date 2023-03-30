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
import inflection.inflection as inf
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

region = "us-east-1"
host = "search-photoscf-dzv7stkzlfny5xr77e4f357dte.us-east-1.es.amazonaws.com/"
index = "photoscf"

lexv2 = boto3.client("lexv2-runtime")
def lambda_handler(event, context):
    print(event)
    msg_from_user = event["queryStringParameters"]["q"]
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
                            keywords.append(inf.singularize(word))
                    else:
                        keywords.append(inf.singularize(key_words))
    # lex delete query3
    print(keywords)
    img_paths = []
    if keywords:
        img_paths = search_photos(keywords)

    if not img_paths:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'results': "No Results found"})
        }
    else:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*',
            },
            'body': json.dumps({'results': img_paths})
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
        response = opensearch.search(body=query, index="photoscf")
        print(response)
        hits = response['hits']['hits']
        img_list = []
        for element in hits:
            objectKey = element['_source']['objectKey']
            bucket = element['_source']['bucket']
            image_url = "https://" + bucket + ".s3.amazonaws.com/" + objectKey
            img_list.append(image_url)
        return img_list

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
