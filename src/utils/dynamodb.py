import os

import boto3

_dynamodb_resource = None
_table = None


def get_dynamodb_resource():
    global _dynamodb_resource
    if _dynamodb_resource is None:
        endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")
        if endpoint_url:
            _dynamodb_resource = boto3.resource(
                "dynamodb",
                endpoint_url=endpoint_url,
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "local"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "local"),
            )
        else:
            _dynamodb_resource = boto3.resource(
                "dynamodb",
                region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
    return _dynamodb_resource


def get_table():
    global _table
    if _table is None:
        table_name = os.environ.get("DYNAMODB_TABLE_NAME", "RecipeManagerTable")
        _table = get_dynamodb_resource().Table(table_name)
    return _table


def reset_clients():
    """Reset clients (useful for testing)."""
    global _dynamodb_resource, _table
    _dynamodb_resource = None
    _table = None
