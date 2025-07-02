import os

class EnvSettings:
    ACCOUNT_ID =  os.getenv('CDK_DEFAULT_ACCOUNT') 
    ACCOUNT_REGION = "us-east-2"
    RAG_PROJ_NAME = "kb-cdk"
