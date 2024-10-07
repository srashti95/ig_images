import pytest
import json
import boto3
from moto import mock_s3, mock_dynamodb2

from handle_ig_images.api.lambdas.delete_image import lambda_handler


@pytest.fixture
def setup_aws_resources():
    region = 'us-west-2'

    with mock_dynamodb2(), mock_s3():
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

        s3 = boto3.client('s3', region_name=region)
        bucket_name = 'ig-images'
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})

        yield bucket_name


def test_upload_image_success(setup_aws_resources):
    bucket_name = setup_aws_resources
    event = {
        'body': json.dumps({
            'image': 'fake_image_data',
            'userId': 'user123',
            'description': 'A sample image',
            'tags': ['sample', 'image']
        })
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert 'imageId' in body
    assert body['message'] == 'Image uploaded successfully'

    s3 = boto3.client('s3', region_name='us-west-2')
    s3_object = s3.get_object(Bucket=bucket_name, Key=f'images/{body["imageId"]}.jpg')
    assert s3_object['Body'].read().decode('utf-8') == 'fake_image_data'

    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('UserImages')
    result = table.get_item(Key={'imageId': body['imageId']})
    assert 'Item' in result
    assert result['Item']['userId'] == 'user123'
    assert result['Item']['description'] == 'A sample image'
    assert result['Item']['tags'] == ['sample', 'image']


def test_upload_image_invalid_input(setup_aws_resources):
    event = {
        'body': json.dumps({
        })
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == 'Invalid input'
