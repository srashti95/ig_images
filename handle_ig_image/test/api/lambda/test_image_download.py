import pytest
import json
import boto3
from moto import mock_s3

from handle_ig_images.api.lambdas.delete_image import lambda_handler


@pytest.fixture
def s3_setup():
    with mock_s3():
        region = 'us-west-2'
        boto3.setup_default_session(region_name=region)

        s3 = boto3.client('s3', region_name=region)
        bucket_name = 'ig-images'
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})

        s3.put_object(Bucket=bucket_name, Key='images/test_image.jpg', Body=b'fake_image_data')
        yield bucket_name


def test_download_image_success(s3_setup):
    event = {
        'pathParameters': {'imageId': 'test_image'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    assert response['headers']['Content-Type'] == 'image/jpeg'
    assert response['headers']['Content-Disposition'] == 'attachment; filename="images/test_image.jpg"'
    assert response['isBase64Encoded'] is True
    assert response['body'] == b'fake_image_data'


def test_download_image_not_found(s3_setup):
    event = {
        'pathParameters': {'imageId': 'nonexistent_image'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 404
    error_response = json.loads(response['body'])
    assert 'error' in error_response
