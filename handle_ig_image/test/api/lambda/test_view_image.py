import pytest
import json
import boto3
from moto import mock_s3

from handle_ig_images.api.lambdas.delete_image import lambda_handler


@pytest.fixture
def setup_aws_resources():
    region = 'us-west-2'

    with mock_s3():
        s3 = boto3.client('s3', region_name=region)
        bucket_name = 'ig-images'
        s3.create_bucket(Bucket=bucket_name)

        image_id = 'example_image_id'
        image_key = f'images/{image_id}.jpg'
        s3.put_object(Bucket=bucket_name, Key=image_key, Body=b'fake_image_data', ContentType='image/jpeg')

        yield bucket_name


def test_view_image_success(setup_aws_resources):
    bucket_name = setup_aws_resources
    event = {
        'pathParameters': {'imageId': 'example_image_id'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    assert response['headers']['Content-Type'] == 'image/jpeg'
    assert response['headers']['Content-Disposition'] == 'inline; filename="example_image_id.jpg"'
    assert response['isBase64Encoded'] is True
    image_data = response['body']
    assert image_data == 'ZmFrZV9pbWFnZV9kYXRh'


def test_view_image_not_found(setup_aws_resources):
    bucket_name = setup_aws_resources
    event = {
        'pathParameters': {'imageId': 'nonexistent_image_id'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert body[
               'error'] == ('Image not found: An error occurred (NoSuchKey) when calling the GetObject operation: The '
                            'specified key does not exist.')
