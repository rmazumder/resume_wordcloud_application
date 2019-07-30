import json
import boto3

def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message'];
    print('Message received from SNS:', message); 
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('resumewordcloudTable')
    response = table.get_item(Key={'name': key})
    item = response['Item']
    message = item['text']
    
    
    //your code
    
    
    
    
    tem = {}
    tem['x'] = 'X'
    tem['y'] = 'y'
    tem['z'] = 'r'
    tem['w'] =  'w'
    item['extraHeader'] = tem
    print(item)
    table.put_item(Item=item)
    print("UpdateItem succeeded:")

