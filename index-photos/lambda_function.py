import json
import boto3
import requests
import random
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    # TODO implement
    photo = event["Records"][0]["s3"]["object"]["key"]
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    timestamp = event["Records"][0]["eventTime"]
    print(photo,bucket)
    labels = detect_labels(photo, bucket)
    s3client = boto3.client('s3')
    customLabels = []
    try:
        labelMetadata = s3client.head_object(Bucket=bucket, Key=photo)["ResponseMetadata"]['HTTPHeaders']['x-amz-meta-customlabels']
        customLabels = labelMetadata.split(", ")
    except:
        customLabels = []
    for customLabel in customLabels:
        labels.append(customLabel)
    
    response = {"objectKey": photo,
                "bucket": bucket,
                "createdTimestamp": timestamp,
                "labels": labels}
    print(response)
    opensearch_insert(response,photo)

    
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
    
    
def opensearch_insert(data,id):
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session(aws_access_key_id="",
                                aws_secret_access_key="", 
                                region_name=region).get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    host = 'https://search-photos-7ybnevwwkhnsfz65yht253leke.us-east-1.es.amazonaws.com'
    index = 'photos'
    url = host + '/' + index + '/_doc/' +  id   
    headers = { "Content-Type": "application/json" }
    
    response = requests.post(url,auth=awsauth, headers=headers, json=data)
    print(response.json())
    
    
def get_s3_metadata(bucket,photo):
    client = boto3.client('s3')
    response = client.head_object(Bucket=bucket, Key=photo)
    if response and "ResponseMetadata" in response and "x-amz-meta-customLabels" in response["ResponseMetadata"]:
        return response["ResponseMetadata"]["x-amz-meta-customLabels"]
    else:
        return None

def detect_labels(photo, bucket):

    client=boto3.client('rekognition')

    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=10)
    return [x["Name"] for x in response['Labels']]

