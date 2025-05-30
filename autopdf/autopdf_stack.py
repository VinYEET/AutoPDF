import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_s3_notifications as s3n,
    aws_sns as sns,
    aws_apigateway as apigw,
    aws_dynamodb as ddb,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct

class AutoPDFStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1) S3 Bucket (auto-expire after 1 day)
        bucket = s3.Bucket(self, "PDFUploadBucket",
            lifecycle_rules=[ s3.LifecycleRule(expiration=Duration.days(1)) ]
        )
    
        # 2) SNS Topic for alerts (optional)
        topic = sns.Topic(self, "PDFNotificationTopic")

        # 3) DynamoDB table for metadata
        meta_table = ddb.Table(self, "MetadataTable",
            partition_key=ddb.Attribute(name="s3Key", type=ddb.AttributeType.STRING),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # 4) DynamoDB table to track monthly OCR usage
        usage_table = ddb.Table(self, "OcrUsageTable",
            partition_key=ddb.Attribute(name="month", type=ddb.AttributeType.STRING),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # 5) PDF‐processing Lambda
        pdf_lambda = lambda_.Function(self, "PDFProcessorLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.main",
            code=lambda_.Code.from_asset("lambda/process_pdf"),
            environment={
                "TOPIC_ARN":         topic.topic_arn,
                "METADATA_TABLE":    meta_table.table_name,
                "OCR_USAGE_TABLE":   usage_table.table_name,
                "OCR_PAGE_LIMIT":    "1000"
            },
        )
        # Permissions for PDF Lambda
        bucket.grant_read(pdf_lambda)
        topic.grant_publish(pdf_lambda)
        meta_table.grant_write_data(pdf_lambda)
        usage_table.grant_read_write_data(pdf_lambda)
        pdf_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=["textract:DetectDocumentText"],
            resources=["*"],
        ))
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(pdf_lambda)
        )

        # 6) Presign Lambda + API Gateway
        presign_fn = lambda_.Function(self, "PresignLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambda/presign"),
            environment={"BUCKET": bucket.bucket_name},
        )
        bucket.grant_put(presign_fn)

        api = apigw.LambdaRestApi(self, "PresignApi",
            rest_api_name="AutoPDF Presign Service",
            handler=presign_fn,
            proxy=False
        )
        presign = api.root.add_resource("presign")
        presign.add_method("GET")
        CfnOutput(self, "PresignEndpoint",
            value=api.url + "presign",
            description="GET /presign?filename="
        )

        # 7) Metadata‐fetch Lambda + route
        get_meta_fn = lambda_.Function(self, "GetMetadataLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambda/get_metadata"),
            environment={"METADATA_TABLE": meta_table.table_name},
        )
        meta_table.grant_read_data(get_meta_fn)

        metadata = api.root.add_resource("metadata")
        metadata.add_method("GET", apigw.LambdaIntegration(get_meta_fn))

        CfnOutput(self, "MetadataEndpoint",
            value=api.url + "metadata",
            description="GET /metadata?key=<s3Key>"
        )
