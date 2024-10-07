import pytest
import json
import boto3
from moto import mock_dynamodb2

from handle_ig_images.api.lambdas.delete_image import lambda_handler


@pytest.fixture
def dynamodb_setup():
    with mock_dynamodb2():
        region = 'us-west-2'
        boto3.setup_default_session(region_name=region)

        dynamodb = boto3.resource('dynamodb', region_name=region)
        table = dynamodb.create_table(
            TableName='UserImages',
            KeySchema=[
                {
                    'AttributeName': 'imageId',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'imageId',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 1,
                'WriteCapacityUnits': 1
            }
        )

        table.put_item(Item={
            'imageId': 'test_image_id',
            'imageUrl': 'http://test.com/image.jpg',
            'description': 'An Test image',
            'tags': ['test', 'image']
        })

        yield


def test_get_image_success(dynamodb_setup):
    event = {
        'pathParameters': {'imageId': 'test_image_id'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['imageId'] == 'test_image_id'
    assert body['imageUrl'] == 'http://test.com/image.jpg'
    assert body['description'] == 'An Test image'
    assert body['tags'] == ['test', 'image']


def test_get_image_not_found(dynamodb_setup):
    event = {
        'pathParameters': {'imageId': 'nonexistent_image_id'}
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == 'Image not found'
