from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
)
from constructs import Construct
from config import DsConfig

bucket_name = DsConfig.S3_BUCKET_NAME
class S3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        bucket = s3.Bucket(self, bucket_name,
                            bucket_name=bucket_name,
                            removal_policy=RemovalPolicy.DESTROY,
                            auto_delete_objects=True)
        
        s3deploy.BucketDeployment(self, "deploy-chatbot-bucket",
            sources=[s3deploy.Source.asset("./sagemaker_documentation")],
            destination_bucket=bucket,
        )
