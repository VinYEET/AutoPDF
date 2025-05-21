import aws_cdk as core
import aws_cdk.assertions as assertions

from auto_pdf.auto_pdf_stack import AutoPdfStack

# example tests. To run these tests, uncomment this file along with the example
# resource in auto_pdf/auto_pdf_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AutoPdfStack(app, "auto-pdf")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
