import json
import boto3
import requests
import random
import time
from requests_aws4auth import AWS4Auth
client = boto3.client('lexv2-runtime')
def lambda_handler(event, context):
    # TODO implement
    print("event:",event)
    msg_from_user = event["q"]
    id = str(hash(str(time.time())))
    response = client.recognize_text(
            botId='MZA1AGTCLT', # MODIFY HERE
            botAliasId='2S2N5W26VO', # MODIFY HERE
            localeId='en_US',
            sessionId=id,
            text=msg_from_user)
    slots = response['sessionState']['intent']['slots']
    label1 = None
    label2 = None
    if "label1" in slots and slots["label1"]:
        label1 = slots['label1']["value"]["interpretedValue"]
    if "label2" in slots and slots["label2"]:
        label2 = slots['label2']["value"]["interpretedValue"]    
    labels = set()
    print("labels:",label1,label2)
    result = set()
    if label1:
        labels.add(label1)
        result = set(opensearch_get(label1))
        if label1[-1]=='s':
            result = result.union(set(opensearch_get(label1[:-1])))

    if label2:
        labels.add(label2)
        result = result.union(set(opensearch_get(label2)))
        if label2[-1]=='s':
            result = result.union(set(opensearch_get(label2[:-1])))
    return {
        'statusCode': 200,
        'headers': { 
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': list(result)
    }


def opensearch_get(data):
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session(aws_access_key_id="",
                                aws_secret_access_key="", 
                                region_name=region).get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    host = 'https://search-photos-7ybnevwwkhnsfz65yht253leke.us-east-1.es.amazonaws.com'
    index = 'photos'
    url = host + '/' + index + '/_search'    
    query = {
        "size": 1000,
        "query": {
            "query_string": {
                "default_field": "labels",
                "query": "*" "*"+data+"*"
            }
        }
    }
    
    headers = { "Content-Type": "application/json" }
    response = requests.get(url,auth=awsauth, headers=headers, data=json.dumps(query))
    print(response.json())

    return [x["_id"] for x in response.json()["hits"]["hits"]]