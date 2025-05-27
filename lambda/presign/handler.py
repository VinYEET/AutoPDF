import os, json, boto3, urllib.parse

s3 = boto3.client("s3")

def handler(event, context):
    # 1. Read & validate the filename param
    params   = event.get("queryStringParameters") or {}
    raw_name = params.get("filename")
    if not raw_name:
        return {"statusCode": 400, "body": "filename query parameter is required"}

    # 2. Decode it (spaces, %28/%29, etc.)
    name = urllib.parse.unquote_plus(raw_name)
    key  = name

    # 3. Generate a presigned PUT URL valid for 1 hour
    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": os.environ["BUCKET"],
            "Key":    key,
            "ContentType": "application/pdf"
        },
        ExpiresIn=3600
    )

    # 4. Return the URL and the key
    return {
        "statusCode": 200,
        "headers":    {"Content-Type": "application/json"},
        "body":       json.dumps({"url": url, "key": key})
    }
