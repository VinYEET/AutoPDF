import os
import json
import urllib.parse
from io import BytesIO
from datetime import datetime

import boto3
import PyPDF2

# AWS clients
s3        = boto3.client("s3")
sns       = boto3.client("sns")
ddb       = boto3.client("dynamodb")
usage_ddb = boto3.client("dynamodb")
textract  = boto3.client("textract")

# Environment variables
TOPIC_ARN       = os.environ["TOPIC_ARN"]
META_TABLE      = os.environ["METADATA_TABLE"]
USAGE_TABLE     = os.environ["OCR_USAGE_TABLE"]
OCR_PAGE_LIMIT  = int(os.environ["OCR_PAGE_LIMIT"])

# OCR thresholds
MAX_OCR_BYTES = 2 * 1024 * 1024   # only OCR files ≤2 MB

def should_ocr_and_record(num_pages: int, month_key: str) -> bool:
    """
    Atomically increment this month's OCR page count by num_pages, 
    but only if the new total would be <= OCR_PAGE_LIMIT.
    Returns True if increment succeeded, False if limit reached.
    """
    try:
        usage_ddb.update_item(
            TableName=USAGE_TABLE,
            Key={"month": {"S": month_key}},
            UpdateExpression="SET used = if_not_exists(used, :zero) + :inc",
            ConditionExpression="attribute_not_exists(used) OR used < :limit",
            ExpressionAttributeValues={
                ":inc":   {"N": str(num_pages)},
                ":limit": {"N": str(OCR_PAGE_LIMIT)},
                ":zero":  {"N": "0"},
            }
        )
        return True
    except usage_ddb.exceptions.ConditionalCheckFailedException:
        return False

def extract_pdf_metadata(bucket: str, key: str) -> dict:
    # 1) Check object size
    head = s3.head_object(Bucket=bucket, Key=key)
    size = head["ContentLength"]

    # 2) Download & parse with PyPDF2
    data   = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    reader = PyPDF2.PdfReader(BytesIO(data))

    num_pages = len(reader.pages)
    meta      = reader.metadata or {}

    # 3) Try built-in text extraction
    text = reader.pages[0].extract_text() or ""

    # 4) Fallback to Textract if no text & size & monthly limit allow
    if not text.strip() and size <= MAX_OCR_BYTES:
        month_key = datetime.utcnow().strftime("%Y-%m")
        if should_ocr_and_record(num_pages, month_key):
            resp  = textract.detect_document_text(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )
            lines = [b["DetectedText"] for b in resp.get("Blocks", []) if b["BlockType"]=="LINE"]
            text  = " ".join(lines)

    preview = text.replace("\n", " ").strip()[:200]

    return {
        "title":   meta.get("/Title")  or "",
        "author":  meta.get("/Author") or "",
        "pages":   num_pages,
        "preview": preview
    }

def main(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]
        key = urllib.parse.unquote_plus(raw_key)
        # size cap
        head      = s3.head_object(Bucket=bucket, Key=key)
        size      = head["ContentLength"]
        MAX_BYTES = 5 * 1024 * 1024
        if size > MAX_BYTES:
            print(f"[WARN] Skipping {key}: size {size} > {MAX_BYTES}")
            continue
        
        try:
            # Extract (and potentially OCR‐augment) the text
            md = extract_pdf_metadata(bucket, key)

            # Write metadata to DynamoDB
            ddb.put_item(
                TableName=META_TABLE,
                Item={
                    "s3Key":    {"S": key},
                    "uploaded": {"S": datetime.utcnow().isoformat()},
                    "title":    {"S": md["title"]},
                    "author":   {"S": md["author"]},
                    "pages":    {"N": str(md["pages"])},
                    "preview":  {"S": md["preview"]},
                }
            )

            # Notify via SNS (optional)
            payload = {"s3Path": f"s3://{bucket}/{key}", "metadata": md}
            sns.publish(TopicArn=TOPIC_ARN, Message=json.dumps(payload), Subject="AutoPDF PDF Uploaded")

        except Exception as e:
            err = {"s3Path": f"s3://{bucket}/{key}", "error": str(e)}
            print("[ERROR] Failed to process PDF:", json.dumps(err))
            sns.publish(TopicArn=TOPIC_ARN, Message=json.dumps(err), Subject="AutoPDF PDF Processing Failed")

    return {"status": "ok"}
