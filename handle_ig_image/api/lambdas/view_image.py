import json
import boto3
from botocore.exceptions import ClientError


class ViewImage:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name

    def handler(self, event, context):
        image_id = event['pathParameters']['imageId']
        image_key = f'images/{image_id}.jpg'

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=image_key)
            image_data = response['Body'].read()

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'image/jpeg',
                    'Content-Disposition': f'inline; filename="{image_id}.jpg"'
                },
                'body': image_data,
                'isBase64Encoded': True
            }
        except ClientError as e:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Image not found: {str(e)}'})
            }


def lambda_handler(event, context):
    bucket_name = 'ig-images'
    viewer = ViewImage(bucket_name)
    return viewer.handler(event, context)
