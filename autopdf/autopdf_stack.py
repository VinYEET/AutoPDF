from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_s3_notifications as s3n,
    aws_sns as sns,
)
from constructs import Construct

class AutoPDFStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 1. S3 Bucket
        bucket = s3.Bucket(self, "PDFUploadBucket")

        # 2. SNS Topic
        topic = sns.Topic(self, "PDFNotificationTopic")

        # 3. Lambda Function
        pdf_lambda = lambda_.Function(
            self, "PDFProcessorLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="handler.main",
            code=lambda_.Code.from_asset("lambda/process_pdf"),
            environment={
                "TOPIC_ARN": topic.topic_arn
            },
        )

        # 4. Permissions
        bucket.grant_read(pdf_lambda)
        topic.grant_publish(pdf_lambda)

        # 5. S3 → Lambda Trigger
        notification = s3n.LambdaDestination(pdf_lambda)
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED, notification)