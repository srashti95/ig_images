import json
import boto3
from botocore.exceptions import ClientError


class ImageDownloader:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name

    def download_image(self, image_key):
        if not self.bucket_name or not image_key:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Bucket name and image key are required.'}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

        try:
            # Generate a pre-signed URL for the S3 object
            url = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.bucket_name, 'Key': image_key},
                                                        ExpiresIn=3600)  # URL expires in 1 hour

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Pre-signed URL generated successfully!',
                    'url': url
                }),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)}),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }


def lambda_handler(event, context):
    bucket_name = 'ig-images'
    image_key = event.get('pathParameters', {}).get('imageKey')
    downloader = ImageDownloader(bucket_name)

    return downloader.download_image(image_key)
