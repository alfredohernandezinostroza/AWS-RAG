import os
from typing import Dict
from boto3 import client
import json

bedrock_agent_runtime_client = client("bedrock-agent-runtime", region_name=os.environ["AWS_REGION"])

def lambda_handler(event, context):
    question = json.loads(event["body"])["question"]

    response = bedrock_agent_runtime_client.retrieve_and_generate(
        input={
            'text': question
        },  
        retrieveAndGenerateConfiguration = {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": os.environ["KNOWLEDGE_BASE_ID"],
                "modelArn": f"arn:aws:bedrock:{os.environ['AWS_REGION']}:{os.environ['USER_ID']}:inference-profile/us.amazon.nova-micro-v1:0"
            }
        }
    )

    return {
        "response": response
    }

