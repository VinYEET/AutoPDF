import os
import json
import boto3
import PyPDF2

sns = boto3.client('sns')
s3  = boto3.client('s3')

def extract_pdf_metadata(bucket, key):
    # Download PDF from S3
    obj = s3.get_object(Bucket=bucket, Key=key)
    reader = PyPDF2.PdfReader(obj['Body'])

    meta      = reader.metadata or {}
    num_pages = len(reader.pages)

    # Optional: grab first 200 chars of text from page 1
    preview = ""
    if reader.pages:
        text = reader.pages[0].extract_text() or ""
        preview = text.replace("\n", " ").strip()[:200]

    return {
        "title":    meta.get("/Title"),
        "author":   meta.get("/Author"),
        "pages":    num_pages,
        "preview":  preview
    }

def main(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key    = record["s3"]["object"]["key"]

        # 1. Extract
        md = extract_pdf_metadata(bucket, key)

        # 2. Build message payload
        payload = {
            "s3Path":   f"s3://{bucket}/{key}",
            "metadata": md
        }

        # 3. Log & notify
        print("[INFO] Extracted metadata:", json.dumps(md))
        sns.publish(
            TopicArn=os.environ["TOPIC_ARN"],
            Message=json.dumps(payload),
            Subject="AutoPDF PDF Uploaded"
        )

    return {"status": "ok"}
