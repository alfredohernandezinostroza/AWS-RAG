#!/usr/bin/env python3
import os

import aws_cdk as cdk

from config import EnvSettings
from chatbot_stacks.s3Stack import S3Stack
from chatbot_stacks.kb_role_stack import KbRoleStack
from chatbot_stacks.oss_infra_stack import OpenSearchServerlessStack
from chatbot_stacks.kb_infra_stack import KbInfraStack

app = cdk.App()
S3Stack(app, "S3Stack",
    env=cdk.Environment(account=EnvSettings.ACCOUNT_ID, region=EnvSettings.ACCOUNT_REGION),
    )

#IAM Role
kbRole_stack = KbRoleStack(app, "KbRoleStack")

# setup vector store
infra_stack = OpenSearchServerlessStack(app, "OpenSearchServerlessStack")

# create Knowledgebase and datasource
kbInfra_stack = KbInfraStack(app, "KbInfraStack")

# set up dependencies 
infra_stack.add_dependency(kbRole_stack)
# infra_stack.add_dependency(chatbot1_stack)
kbInfra_stack.add_dependency(infra_stack)

app.synth()
