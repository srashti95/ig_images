import json
import boto3
from botocore.exceptions import ClientError


class DeleteImage:
    def __init__(self, bucket_name, table_name):
        self.s3_client = boto3.client('s3')
        self.dynamodb_client = boto3.resource('dynamodb')
        self.bucket_name = bucket_name
        self.table_name = table_name

    def handler(self, event, context):
        image_id = event['pathParameters']['imageId']
        image_key = f'images/{image_id}.jpg'

        try:
            self.dynamodb_client.Table(self.table_name).delete_item(Key={'imageId': image_id})
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to delete from DynamoDB: {str(e)}'})
            }

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=image_key)
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to delete from S3: {str(e)}'})
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Image deleted successfully'})
        }


def lambda_handler(event, context):
    bucket_name = 'ig-images'
    table_name = 'UserImages'
    deleter = DeleteImage(bucket_name, table_name)
    return deleter.handler(event, context)
