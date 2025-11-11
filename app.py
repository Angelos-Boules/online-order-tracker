#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stack import Stack   

app = cdk.App()
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)
Stack(app, "Stack", env=env, project_name="mfox-test")
app.synth()
