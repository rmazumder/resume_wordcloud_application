import json
import boto3
import os
from urllib.parse import unquote_plus

DYNAMODB_TABLE = os.environ.get('DYNAMO_DB_TABLE',"resume-metadata-prod")

def lambda_handler(event, context):
    print("Delete resume invoked")
    print(event)
    s3 = boto3.resource('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    key = unquote_plus(key)
    imagekey = key.replace("resume", "image")+".png"
    obj = s3.Object(bucket, imagekey)
    print(obj)
    obj.delete()
    print("image file deleted " + imagekey)
    dynamodb = boto3.resource('dynamodb')
    print("Deleting resource from dynamoDB " + key)
    table = dynamodb.Table(DYNAMODB_TABLE)
    table.delete_item(Key={'name': key})
    print("Deletion completed")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
