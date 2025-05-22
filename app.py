#!/usr/bin/env python3
import aws_cdk as cdk
from autopdf.autopdf_stack import AutoPDFStack

app = cdk.App()
AutoPDFStack(app, "AutoPDFStack")
app.synth()