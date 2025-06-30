from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct

class Chatbot1Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        bucket = s3.Bucket(self, f"chatbot-bucket-{self.account}", bucket_name=f"chatbot-bucket-{self.account}")
        
        s3deploy.BucketDeployment(self, "deploy-chatbot-bucket",
            sources=[s3deploy.Source.asset("./sagemaker_documentation")],
            destination_bucket=bucket,
        )

        # example resource
        # queue = sqs.Queue(
        #     self, "Chatbot1Queue",
        #     visibility_timeout=Duration.seconds(300),
        # )
