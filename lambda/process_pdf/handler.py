import os
import json
import boto3
import PyPDF2
import urllib.parse
from io import BytesIO
from datetime import datetime

sns = boto3.client("sns")
s3 = boto3.client("s3")
ddb = boto3.client("dynamodb")


def extract_pdf_metadata(bucket, key):
    # Download the PDF into memory
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    stream = BytesIO(data)

    # Parse metadata and page count
    reader = PyPDF2.PdfReader(stream)
    meta = reader.metadata or {}
    num_pages = len(reader.pages)

    # Extract a short text preview from the first page
    preview = ""
    if reader.pages:
        text = reader.pages[0].extract_text() or ""
        preview = text.replace("\n", " ").strip()[:200]

    return {
        "title": meta.get("/Title"),
        "author": meta.get("/Author"),
        "pages": num_pages,
        "preview": preview,
    }


def main(event, context):
    table = os.environ["METADATA_TABLE"]
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]
        # URL-decode the S3 key (handles spaces, parentheses, etc.)
        key = urllib.parse.unquote_plus(raw_key)

        try:
            # Extract metadata
            md = extract_pdf_metadata(bucket, key)

            # 2) Persist into DynamoDB
            ddb.put_item(
                TableName=table,
                Item={
                    "s3Key": {"S": key},
                    "uploaded": {"S": datetime.utcnow().isoformat()},
                    "title": {"S": md.get("title") or ""},
                    "author": {"S": md.get("author") or ""},
                    "pages": {"N": str(md.get("pages", 0))},
                    "preview": {"S": md.get("preview") or ""},
                },
            )
            payload = {"s3Path": f"s3://{bucket}/{key}", "metadata": md}

            print("[INFO] Extracted metadata:", json.dumps(md))
            sns.publish(
                TopicArn=os.environ["TOPIC_ARN"],
                Message=json.dumps(payload),
                Subject="AutoPDF PDF Uploaded",
            )

        except Exception as e:
            # Handle and notify on any errors
            error_payload = {"s3Path": f"s3://{bucket}/{key}", "error": str(e)}
            print("[ERROR] Failed to process PDF:", json.dumps(error_payload))
            sns.publish(
                TopicArn=os.environ["TOPIC_ARN"],
                Message=json.dumps(error_payload),
                Subject="AutoPDF PDF Processing Failed",
            )

    return {"status": "ok"}
