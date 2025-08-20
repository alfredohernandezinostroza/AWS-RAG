
# LLM RAG

This repository contains an implementation of a LLM-based chatbot with Retrieval Augmented Generation. It relies on several AWS Services: Amazon S3, Bedrock Knowledge Bases, and OpenSearch Service.

The diagram of the architecture is as follows:

![diagram](diagram_export.svg)


In ./Deployment, the source code for the code developed using AWS CDK is available to deploy the resources. First, the requirements inside deployments can be installed in a python virtual environement with:

```python -m venv```

```source .venv/bin/active```

```python -m pip install -r requirements.txt```

Then, the code can be deployed to a bootstrapped AWS environment with:

```cdk deploy --all```

(This assumes the current active CDK profile has the same region as the one in Deployment/config.py/)

In ./Frontend, a simple chat application has been included for demonstration purposes. It can be served as a static website. The only modification it needs to work is to fill the ``backend_url`` variable with the lambda url generated.
