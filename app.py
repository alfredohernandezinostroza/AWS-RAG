#!/usr/bin/env python3
import os

import aws_cdk as cdk

from config import EnvSettings
from chatbot_stacks.S3Stack import S3Stack


app = cdk.App()
S3Stack(app, "S3Stack",
    env=cdk.Environment(account=EnvSettings.ACCOUNT_ID, region=os.getenv('CDK_DEFAULT_REGION')),
    )

app.synth()
