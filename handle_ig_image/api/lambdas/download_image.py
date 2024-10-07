import json
import boto3
from botocore.exceptions import ClientError


class ImageDownloader:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name

    def download_image(self, image_key):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=image_key)
            image_content = response['Body'].read()

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'image/jpeg',
                    'Content-Disposition': f'attachment; filename="{image_key}"'
                },
                'body': image_content,
                'isBase64Encoded': True
            }

        except ClientError as e:
            return {
                'statusCode': e.response['ResponseMetadata']['HTTPStatusCode'],
                'body': json.dumps({'error': str(e)})
            }


def lambda_handler(event, context):
    bucket_name = 'ig-images'
    image_key = event.get('pathParameters', {}).get('imageKey')
    downloader = ImageDownloader(bucket_name)

    return downloader.download_image(image_key)
