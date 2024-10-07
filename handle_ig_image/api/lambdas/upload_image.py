import json
import boto3
import uuid
from botocore.exceptions import ClientError


class UploadImage:
    def __init__(self, bucket_name, table_name):
        self.s3_client = boto3.client('s3')
        self.dynamodb_client = boto3.resource('dynamodb')
        self.bucket_name = bucket_name
        self.table_name = table_name

    def handler(self, event, context):
        try:
            body = json.loads(event['body'])
            image_data = body['image']
            user_id = body['userId']
            description = body['description']
            tags = body['tags']
        except (KeyError, json.JSONDecodeError):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid input'})
            }

        image_id = str(uuid.uuid4())
        image_key = f'images/{image_id}.jpg'

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=image_key,
                Body=image_data.encode('utf-8'),
                ContentType='image/jpeg'
            )
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

        metadata = {
            'imageId': image_id,
            'userId': user_id,
            'description': description,
            'tags': tags,
            'imageUrl': f'https://{self.bucket_name}.s3.amazonaws.com/{image_key}'
        }
        self.dynamodb_client.Table(self.table_name).put_item(Item=metadata)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Image uploaded successfully', 'imageId': image_id})
        }


def lambda_handler(event, context):
    bucket_name = 'ig-images'
    table_name = 'UserImages'
    uploader = UploadImage(bucket_name, table_name)
    return uploader.handler(event, context)
