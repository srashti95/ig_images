import json
import logging

import boto3

logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class GetImage:
    def __init__(self, table_name):
        self.dynamodb_client = boto3.resource('dynamodb')
        self.table_name = table_name

    def handler(self, event, context):
        try:
            image_id = event['pathParameters']['imageId']
            table = self.dynamodb_client.Table(self.table_name)

            response = table.get_item(Key={'imageId': image_id})
            item = response.get('Item')

            if not item:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Image not found'})
                }

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'imageId': item['imageId'],
                    'imageUrl': item['imageUrl'],
                    'description': item.get('description'),
                    'tags': item.get('tags')
                })
            }

        except Exception as e:
            logger.warn(f"Exception Caught {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }


def lambda_handler(event, context):
    table_name = 'UserImages'
    getter = GetImage(table_name)
    return getter.handler(event, context)
