import json
import boto3
from boto3.dynamodb.conditions import Key


class ListImages:
    def __init__(self, table_name):
        self.dynamodb_client = boto3.resource('dynamodb')
        self.table_name = table_name

    def handler(self, event, context):
        table = self.dynamodb_client.Table(self.table_name)

        user_id = event.get('queryStringParameters', {}).get('userId')
        tags = event.get('queryStringParameters', {}).get('tags')

        try:
            filtered_images = []

            if user_id:
                response = table.query(
                    IndexName='userId-index',  # Ensure you have a Global Secondary Index for userId
                    KeyConditionExpression=Key('userId').eq(user_id)
                )
                filtered_images.extend(response.get('Items', []))
            else:
                response = table.scan()
                filtered_images.extend(response.get('Items', []))

            if tags:
                tag_list = tags.split(',')
                filtered_images = [
                    item for item in filtered_images
                    if any(tag in item.get('tags', []) for tag in tag_list)
                ]

            return {
                'statusCode': 200,
                'body': json.dumps(filtered_images)
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to list images: {str(e)}'})
            }


def lambda_handler(event, context):
    table_name = 'UserImages'
    lister = ListImages(table_name)
    return lister.handler(event, context)
