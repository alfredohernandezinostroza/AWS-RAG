from constructs import Construct

from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ssm as ssm,
    aws_events as events,
)

from aws_cdk import aws_bedrock as bedrock

from aws_cdk.aws_bedrock import (
  CfnKnowledgeBase,
  CfnDataSource
)
import json
from config import EnvSettings, KbConfig, DsConfig, OpenSearchServerlessConfig

region = EnvSettings.ACCOUNT_REGION
account_id = EnvSettings.ACCOUNT_ID

vector_store_type = KbConfig.VECTOR_STORE_TYPE

collectionName = OpenSearchServerlessConfig.COLLECTION_NAME
indexName = OpenSearchServerlessConfig.INDEX_NAME

embeddingModelId = KbConfig.EMBEDDING_MODEL_ID
parsing_strategy = KbConfig.PARSING_STRATEGY

max_tokens = KbConfig.MAX_TOKENS
overlap_percentage = KbConfig.OVERLAP_PERCENTAGE

class KbInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        
        # Get the partition dynamically
        partition = Stack.of(self).partition

        # Construct ARNs using the correct partition
        self.embedding_model_arn = f"arn:{partition}:bedrock:{region}::foundation-model/{embeddingModelId}"
        self.parser_model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        self.s3_bucket_arn = f"arn:{partition}:s3:::{DsConfig.S3_BUCKET_NAME}"

        self.kbRoleArn = ssm.StringParameter.from_string_parameter_attributes(
            self, 
            "kbRoleArn",
            parameter_name="/e2e-rag/kbRoleArn"
        ).string_value
                        
        # Create Knowledgebase
        
        # initialize knowledge base with default value
        self.knowledge_base = None
        self.collectionArn = ssm.StringParameter.from_string_parameter_attributes(
            self, 
            "collectionArn",
            parameter_name="/e2e-rag/collectionArn"
        ).string_value
        self.knowledge_base = self.create_knowledge_base_oss()
        self.data_source = self.create_data_source(self.knowledge_base)

        self.ingest_lambda = self.create_ingest_lambda( self.knowledge_base, self.data_source)
        self.query_lambda = self.create_query_lambda(self.knowledge_base)

    
    def create_knowledge_base_oss(self) -> CfnKnowledgeBase:
        print("Creating knowledge base with OSS vector store....")
        supplemental_data_storage_configuration = []
        return CfnKnowledgeBase(
            self, 
            'e2eRagKB',
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=self.embedding_model_arn,
                    supplemental_data_storage_configuration=supplemental_data_storage_configuration
                )
            ),
            name='MyKnowledgeBaseOSS',
            role_arn=self.kbRoleArn,
            description='e2e multi-modal RAG Knowledge base with OSS',
            storage_configuration=CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=self.collectionArn,
                    field_mapping=bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        metadata_field="AMAZON_BEDROCK_METADATA",
                        text_field="AMAZON_BEDROCK_TEXT_CHUNK",
                        vector_field="bedrock-knowledge-base-default-vector"
                    ),
                    vector_index_name=indexName
                )
            )
        )

    def create_data_source(self, knowledge_base) -> CfnDataSource:
        print("Creating data source...")
        kbid = knowledge_base.attr_knowledge_base_id
        chunking_strategy = KbConfig.CHUNKING_STRATEGY
        parsing_configuration = None
        print("Parsing configuration: ",parsing_configuration)

        if chunking_strategy == "Fixed-size chunking":
            vector_ingestion_config = bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="FIXED_SIZE",
                    fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=max_tokens,
                        overlap_percentage=overlap_percentage
                    )
                ),
                parsing_configuration = parsing_configuration
            )
        elif chunking_strategy == "Default chunking":
            vector_ingestion_config = bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="FIXED_SIZE",
                    fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=300,
                        overlap_percentage=20
                    )
                ),
                parsing_configuration = parsing_configuration
            )
        else:
            vector_ingestion_config = bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                    chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                        chunking_strategy="NONE"
                    ),
                    parsing_configuration = parsing_configuration
                )

        return CfnDataSource(
            self, 
            "e2eRagDataSource",
            data_source_configuration=CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=self.s3_bucket_arn,
                ),
                type="S3"
            ),
            knowledge_base_id=kbid,
            name="e2eRAGDataSource",
            description="e2eRAG DataSource",
            vector_ingestion_configuration=vector_ingestion_config
        )
  
  # Below functions can be used if you need to integrate lambda functions for ingestion and querying 
    def create_ingest_lambda(self, knowledge_base, data_source) -> lambda_:
        ingest_lambda = lambda_.Function(
            self,
            "IngestionJob",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="ingestJobLambda.lambda_handler",
            code=lambda_.Code.from_asset("./lambda_functions/IngestJob"),
            timeout=Duration.minutes(5),
            environment={
                "KNOWLEDGE_BASE_ID": knowledge_base.attr_knowledge_base_id,
                "DATA_SOURCE_ID": data_source.attr_data_source_id,
            }
        )

        ingest_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:StartIngestionJob"],
                resources=[knowledge_base.attr_knowledge_base_arn]
            )
        )
        return ingest_lambda

    def create_query_lambda(self, knowledge_base) -> lambda_:
        partition = Stack.of(self).partition
        query_lambda = lambda_.Function(
            self, 
            "Query",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="queryKBLambda.lambda_handler",
            code=lambda_.Code.from_asset("./lambda_functions/queryKnowledgeBase"),
            timeout=Duration.minutes(5),
            environment={
                "KNOWLEDGE_BASE_ID": knowledge_base.attr_knowledge_base_id,
                "USER_ID": EnvSettings.ACCOUNT_ID
            }
        )

        # Function URL configuration with CORS
        fn_url = query_lambda.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            invoke_mode=lambda_.InvokeMode.BUFFERED,
            cors={
                "allowed_origins": ["*"],
                "allowed_methods": [lambda_.HttpMethod.POST],
                "allowed_headers": ['Content-Type']
            }
        )

        # Add permissions for Bedrock
        query_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:RetrieveAndGenerate",
                    "bedrock:Retrieve",
                    "bedrock:InvokeModel",
                ],
                resources=[f"arn:{partition}:bedrock:{region}:*:*"]
            )
        )
        query_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:RetrieveAndGenerate",
                    "bedrock:Retrieve",
                    "bedrock:InvokeModel",
                    "bedrock:GetInferenceProfile"
                ],
                resources=[f"arn:{partition}:bedrock:{region}:*:inference-profile/us.amazon.nova-micro-v1:0"]
            )
        )
        query_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                "bedrock:InvokeModel*",
                "bedrock:CreateInferenceProfile"
                ],
                resources=[
                "arn:aws:bedrock:*::foundation-model/*",
                "arn:aws:bedrock:*:*:inference-profile/*",
                "arn:aws:bedrock:*:*:application-inference-profile/*"
                ]
            )
        )
        query_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                "bedrock:GetInferenceProfile",
                "bedrock:ListInferenceProfiles",
                "bedrock:DeleteInferenceProfile",
                "bedrock:TagResource",
                "bedrock:UntagResource",
                "bedrock:ListTagsForResource"
                ],
                resources=[
                "arn:aws:bedrock:*:*:inference-profile/*",
                "arn:aws:bedrock:*:*:application-inference-profile/*"
                ]
            )
        )

        return query_lambda
  
    def add_eventbridge_rule(self, bucket, lambda_function):
        rule = events.Rule(
            self, 
            "MyRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
            )
        )
        rule.add_target(lambda_function)
        bucket.grant_read(lambda_function)