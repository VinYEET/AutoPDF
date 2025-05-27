import os
import json
import boto3

ddb = boto3.client("dynamodb")

def handler(event, context):
    #  Pull out the `key` query‐param
    params = event.get("queryStringParameters") or {}
    key    = params.get("key")
    if not key:
        return {
            "statusCode": 400,
            "body": "Missing required query parameter: key"
        }

    #  Fetch from DynamoDB
    try:
        resp = ddb.get_item(
            TableName = os.environ["METADATA_TABLE"],
            Key       = {"s3Key": {"S": key}}
        )
    except Exception as e:
        return {"statusCode": 500, "body": f"DynamoDB error: {e}"}

    item = resp.get("Item")
    if not item:
        return {"statusCode": 404, "body": "Metadata not found"}

    #  Convert DynamoDB types back to JSON
    result = {
        "title":   item["title"]["S"],
        "author":  item["author"]["S"],
        "pages":   int(item["pages"]["N"]),
        "preview": item["preview"]["S"],
        "uploaded": item.get("uploaded", {}).get("S")
    }

    return {
        "statusCode": 200,
        "headers":    {"Content-Type": "application/json"},
        "body":       json.dumps(result)
    }
