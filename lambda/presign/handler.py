import os
import json
import boto3
import urllib.parse

# Initialize the S3 client and read the target bucket name from env
s3     = boto3.client("s3")
BUCKET = os.environ["BUCKET"]

def handler(event, context):
    # Read & validate the filename param
    params   = event.get("queryStringParameters") or {}
    raw_name = params.get("filename")
    if not raw_name:
        return {
            "statusCode": 400,
            "body": "filename query parameter is required"
        }

    # Decode URL-encoded filename
    key = urllib.parse.unquote_plus(raw_name)

    # Generate a presigned POST that only allows 1–5 MiB uploads
    post = s3.generate_presigned_post(
        Bucket=BUCKET,
        Key=key,
        Conditions=[
            ["content-length-range", 1, 5 * 1024 * 1024]
        ],
        ExpiresIn=3600
    )

    # Return the POST info + the object key
    return {
        "statusCode": 200,
        "headers":    {"Content-Type": "application/json"},
        "body":       json.dumps({
            "url":    post["url"],
            "fields": post["fields"], 
            "key":    key
        })
    }
