AutoPDF
AutoPDF is a serverless PDF uploader & processor. Users pick a PDF in a browser extension → it uploads to S3 → Lambda extracts metadata and sends an SNS notification.

Quick Start
Clone & enter
git clone https://github.com/<you>/AutoPDF.git
cd AutoPDF

Python & venv
python -m venv .venv
..venv\Scripts\Activate
pip install --upgrade pip
pip install -r requirements-dev.txt

Vendor Lambda deps
pip install -r lambda\process_pdf\requirements.txt -t lambda\process_pdf

AWS creds
aws configure --profile autopdf
or
$Env:AWS_PROFILE = "autopdf"
$Env:AWS_DEFAULT_REGION = "us-east-1"

Deploy
cdk bootstrap --profile autopdf
cdk deploy --profile autopdf

Project Layout
AutoPDF/
├── autopdf/ # CDK stack
├── lambda/process_pdf/ # Lambda code + requirements.txt
├── app.py
├── cdk.json
├── requirements-dev.txt
└── README.md