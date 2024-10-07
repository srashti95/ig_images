from unittest.mock import patch

import pytest
import json
import boto3
from moto import mock_s3, mock_dynamodb2

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


@pytest.fixture
def dynamodb_setup():
    with mock_dynamodb2():
        dynamodb = boto3.resource('dynamodb')
        table_name = 'UserImages'
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'imageId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'imageId', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        bucket_name = 'ig-images'
        table = dynamodb.Table(table_name)
        table.put_item(Item={'imageId': 'test_image', 'bucket': bucket_name, 'key': 'images/test_image.jpg'})
        yield table_name


def test_delete_image_success(s3_setup, dynamodb_setup):
    event = {
        'pathParameters': {'imageId': 'test_image'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    assert 'Image deleted successfully' in json.loads(response['body'])

    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_setup)
    assert 'Contents' not in response  # Should be empty after deletion

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(dynamodb_setup)
    response = table.get_item(Key={'imageId': 'test_image'})
    assert 'Item' not in response


def test_delete_image_dynamodb_error(s3_setup):
    event = {
        'pathParameters': {'imageId': 'nonexistent_image'}
    }

    with pytest.raises(Exception):
        response = lambda_handler(event, None)
        assert response['statusCode'] == 500
        assert 'Failed to delete from DynamoDB' in json.loads(response['body'])


def test_delete_image_s3_error(s3_setup, dynamodb_setup):
    event = {
        'pathParameters': {'imageId': 'test_image'}
    }

    with patch('boto3.client') as mock_client:
        mock_client.return_value.delete_object.side_effect = Exception("S3 error")
        response = lambda_handler(event, None)

        assert response['statusCode'] == 500
        assert 'Failed to delete from S3' in json.loads(response['body'])
