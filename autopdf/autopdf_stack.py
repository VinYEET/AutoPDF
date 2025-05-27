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
    CfnOutput,
)
from constructs import Construct


class AutoPDFStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. S3 Bucket
        bucket = s3.Bucket(
            self,
            "PDFUploadBucket",
            lifecycle_rules=[s3.LifecycleRule(expiration=Duration.days(1))],
        )

        # 2. SNS Topic
        topic = sns.Topic(self, "PDFNotificationTopic")

        # 3. DynamoDB Table for metadata
        table = ddb.Table(
            self,
            "MetadataTable",
            partition_key=ddb.Attribute(name="s3Key", type=ddb.AttributeType.STRING),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # 4. PDF‐processing Lambda
        pdf_lambda = lambda_.Function(
            self,
            "PDFProcessorLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.main",
            code=lambda_.Code.from_asset("lambda/process_pdf"),
            environment={
                "TOPIC_ARN": topic.topic_arn,
                "METADATA_TABLE": table.table_name,
            },
        )

        # 5. Permissions & Trigger
        bucket.grant_read(pdf_lambda)
        topic.grant_publish(pdf_lambda)
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(pdf_lambda)
        )
        table.grant_write_data(pdf_lambda)

        # 6. PRESIGN–URL SERVICE
        # 6a. Presign Lambda
        presign_fn = lambda_.Function(
            self,
            "PresignLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.handler",  # points at lambda/presign/handler.py
            code=lambda_.Code.from_asset("lambda/presign"),
            environment={"BUCKET": bucket.bucket_name},
        )
        bucket.grant_put(presign_fn)

        # 6b. Expose via API Gateway
        api = apigw.LambdaRestApi(
            self,
            "PresignApi",
            rest_api_name="AutoPDF Presign Service",
            handler=presign_fn,
            proxy=False,
        )
        presign = api.root.add_resource("presign")
        presign.add_method("GET")  # GET /presign?filename=

        # 6c. Output the URL for easy reference
        cdk.CfnOutput(
            self,
            "PresignEndpoint",
            value=api.url + "presign",
            description="HTTP GET endpoint to generate S3 presigned URLs",
        )
        
        # 7. METADATA‐FETCH SERVICE
        # 7a. Lambda to read from DynamoDB
        get_meta_fn = lambda_.Function(
            self, "GetMetadataLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambda/get_metadata"),
            environment={"METADATA_TABLE": table.table_name}
        )
        # Grant read‐only permission on your metadata table
        table.grant_read_data(get_meta_fn)

        # 7b. Add `/metadata` to your existing API Gateway
        metadata = api.root.add_resource("metadata")
        metadata.add_method(
            "GET",
            apigw.LambdaIntegration(get_meta_fn),
            # optional: require `key` query‐param documented in usage
        )

        # 7c. Output metadata endpoint
        CfnOutput(self, "MetadataEndpoint",
            value=api.url + "metadata",
            description="GET /metadata?key=<s3Key> to fetch stored PDF metadata"
        )
