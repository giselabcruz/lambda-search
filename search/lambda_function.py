import json
import os
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'Tickets')
PRODUCT_INDEX = os.environ.get('PRODUCT_INDEX')

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        product = extract_product_param(event)
        if not product:
            return build_response(400, {"message": "Missing required parameter 'product'"})
        items = query_by_product(product)
        return build_response(200, {"product": product, "count": len(items), "items": items})
    except Exception:
        return build_response(500, {"message": "Internal server error"})

def extract_product_param(event):
    product = None
    qs = event.get("queryStringParameters")
    if qs:
        product = qs.get("product")
    if not product and event.get("body"):
        try:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
            product = body.get("product")
        except:
            pass
    return product

def query_by_product(product):
    if PRODUCT_INDEX:
        response = table.query(
            IndexName=PRODUCT_INDEX,
            KeyConditionExpression=Key("product").eq(product)
        )
    else:
        response = table.scan(
            FilterExpression=Attr("product").eq(product)
        )
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression=Attr("product").eq(product),
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))
    return items

def build_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body_dict)
    }
