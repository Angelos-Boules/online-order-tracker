# stack.py
from constructs import Construct
from aws_cdk import (
    Stack as CdkStack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    custom_resources as cr,
)


class Stack(CdkStack):
    """
    Core services stack:
      - S3 static website bucket 
      - DynamoDB table 
      - ONE Lambda (Python 3.12) that handles POST and GET on /order
      - API Gateway (REST) 
      - Static site auto-deployed AND gets a config.json with the real API URL

    NOTE:
      - Lambda code is expected in ./lambda_code/order_handler.py
      - index.html lives in ./web/index.html
      - index.html fetches ./config.json to learn the API URL
    """

    # Must change this - this will be the prefix to all allocated AWS resources for the project #
    PROJECT_NAME = "online-order-tracking"
    ###############################################################################################

    def __init__(self, scope: Construct, construct_id: str, *, project_name: str = PROJECT_NAME, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1) S3 static website 
        site_bucket = s3.Bucket(
            self,
            "FrontendHostingBucket",
            website_index_document="index.html", # this was my temp frontend
            public_read_access=True,  
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # 2) DynamoDB (orders)
        table = dynamodb.Table(
            self,
            "OrdersTable",
            table_name=f"{project_name}-orders",
            partition_key=dynamodb.Attribute(name="orderId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # 3) Lambda  — one function handles GET and POST
        handler = _lambda.Function(
            self,
            "OrderHandler",
            function_name=f"{project_name}-order-handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambda_code"), # The lambda code resides in a folder named "lambda_code"
            handler="order_handler.handler",
            environment={"TABLE_NAME": table.table_name},
            memory_size=128,                                
            timeout=Duration.seconds(5),                   
            log_retention=logs.RetentionDays.ONE_WEEK,     
        )
        table.grant_read_write_data(handler)

        # 4) API Gateway (REST) 
        api = apigw.RestApi(
            self,
            "Api",
            rest_api_name=f"{project_name}-api",
            deploy_options=apigw.StageOptions(stage_name="prod"),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            ),
        )

        order = api.root.add_resource("order")
        integration = apigw.LambdaIntegration(handler)
        order.add_method("POST", integration) # POST /order
        order.add_method("GET", integration) # GET /order
        order_by_id = order.add_resource("{id}") # GET /order/{id}
        order_by_id.add_method("GET", integration)

        # 5) Deploy static site assets from ./web
        deploy_site = s3deploy.BucketDeployment(
            self,
            "DeployWebsite",
            destination_bucket=site_bucket,
            sources=[s3deploy.Source.asset("web")],
            destination_key_prefix="",
            prune=False,
            retain_on_delete=False,
        )

        # 6) Write config.json with the real API URL at deploy time
        config_key = "config.json"
        config_body = f'{{"apiBase":"{api.url}order"}}'  

        write_config = cr.AwsCustomResource(
            self, "WriteWebConfig",
            on_update=cr.AwsSdkCall(
                service="S3",
                action="putObject",
                parameters={
                    "Bucket": site_bucket.bucket_name,
                    "Key": config_key,
                    "Body": config_body,
                    "ContentType": "application/json",
                },
                physical_resource_id=cr.PhysicalResourceId.of(f"{project_name}-web-config-v2"), 
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    actions=["s3:PutObject","s3:DeleteObject"],
                    resources=[site_bucket.arn_for_objects(config_key)],
                )
            ]),
        )

        # Ensure the bucket and site content exist before writing config.json
        write_config.node.add_dependency(site_bucket)
        write_config.node.add_dependency(deploy_site)

        # Super Helpful outputs: these will print in the terminal after "cdk deploy" finishes
        CfnOutput(self, "WebsiteURL", value=site_bucket.bucket_website_url)
        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "TableName", value=table.table_name)
        CfnOutput(self, "FunctionName", value=handler.function_name)
        CfnOutput(self, "ConfigUrl", value=f"{site_bucket.bucket_website_url}config.json")
