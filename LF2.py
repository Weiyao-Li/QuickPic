import json
import boto3
from botocore.vendored import requests  # for OpenSearch requests
from urllib.parse import quote_plus  # for URL encoding query

def lambda_handler(event, context):
    # Extract the user's input from the event
    input_text = event['request']['inputTranscript']

    # Call the Lex bot to disambiguate the query
    lex_client = boto3.client('lexv2-runtime')
    lex_response = lex_client.recognize_text(
        botId='5GMXHBNSCD',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId=event['session']['id'],
        text=input_text
    )
    print(lex_response)

    # Get any keywords returned by Lex
    keywords = []
    if 'slots' in lex_response['interpretations'][0]:
        for slot in lex_response['interpretations'][0]['slots']:
            if slot['value'] is not None:
                keywords.append(slot['value']['interpretedValue'])
    print(keywords)

    # Search the OpenSearch index for results
    if keywords:
        # Create the OpenSearch request URL
        url = 'https://photos-search-domain-abcxyz7890123.us-east-1.es.amazonaws.com/photos/_search?q='
        url += ' AND '.join([quote_plus(k) for k in keywords])
        print(url)

        # Send the OpenSearch request
        response = requests.get(url)
        search_results = response.json()['hits']['hits']
    else:
        # Return an empty array if no keywords were found
        search_results = []

    # Format the search results as per the API spec
    formatted_results = []
    for result in search_results:
        photo_url = result['_source']['photo_url']
        photo_title = result['_source']['photo_title']
        formatted_results.append({'url': photo_url, 'title': photo_title})

    # Return the search results as a JSON response
    response_body = {'results': formatted_results}
    response = {
        'sessionState': event['session'],
        'interpretations': [
            {
                'intent': {
                    'name': 'SearchIntent'
                },
                'response': {
                    'messages': [
                        {
                            'contentType': 'PlainText',
                            'content': json.dumps(response_body)
                        }
                    ]
                }
            }
        ]
    }
    return response
