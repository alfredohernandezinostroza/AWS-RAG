import os

class EnvSettings:
    ACCOUNT_ID =  os.getenv('CDK_DEFAULT_ACCOUNT') 
    ACCOUNT_REGION = "us-east-2"
    # ACCOUNT_REGION = os.getenv('CDK_DEFAULT_REGION') #We could use this if we wanted the default region
    RAG_PROJ_NAME = "kb-cdk"
