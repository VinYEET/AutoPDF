# AutoPDF – Secure Document Processor

**AutoPDF** is a serverless PDF uploader and processor designed to work within the AWS Free Tier.  
Users can upload PDFs through a browser extension or UI → files are stored in S3 → AWS Lambda extracts metadata and triggers an SNS notification.  
A React-based frontend with Nutrient's PSPDFKit viewer allows secure annotation and redacted export of documents.

---

## 🚀 Quick Start

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/VinYEET/AutoPDF.git
cd AutoPDF

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows
# source .venv/bin/activate  # On macOS/Linux

# Install dev dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### 2. Vendor Lambda Dependencies

```bash
pip install -r lambda\process_pdf\requirements.txt -t lambda\process_pdf
```

### 3. Configure AWS Credentials

```bash
aws configure --profile autopdf
# or use env variables:
$Env:AWS_PROFILE = "autopdf"
$Env:AWS_DEFAULT_REGION = "us-east-1"
```

### 4. Deploy Infrastructure

```bash
cdk bootstrap --profile autopdf
cdk deploy --profile autopdf
```

---

## 📁 Project Layout

```
AutoPDF/
├── autopdf/                  # CDK infrastructure (S3, Lambda, SNS setup)
│   └── autopdf_stack.py
├── lambda/
│   └── process_pdf/          # Lambda handler and utilities
│       ├── handler.py
│       └── utils.py
├── viewer-frontend/          # React + Nutrient viewer (optional)
│   ├── public/
│   └── src/
│       ├── components/
│       ├── App.jsx
│       ├── index.js
│       └── utils/download.js
├── app.py                    # CDK app entry point
├── cdk.json
├── requirements-dev.txt
├── requirements.txt
└── README.md
```