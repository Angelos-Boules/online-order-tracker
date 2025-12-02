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
    aws_cognito as cognito,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cforigins,
    aws_cloudwatch as cloudwatch,
)


class Stack(CdkStack):
    PROJECT_NAME = "order-tracker"

    def __init__(self, scope: Construct, construct_id: str, *, project_name: str = PROJECT_NAME, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 static website storage
        site_bucket = s3.Bucket(
            self,
            "OrderTrackerFrontend",
            bucket_name=f"{project_name}-frontend",
            public_read_access=False,  
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Cloudfront to serve website with HTTPS
        dist = cloudfront.Distribution(
            self,
            "OrderTrackingDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=cforigins.S3Origin(site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
        )

        # Cognito user pool
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"{project_name}-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=6,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
        )

        cognito.CfnUserPoolDomain(
            self,
            "UserPoolDomain",
            domain=project_name,
            user_pool_id=user_pool.user_pool_id,
        )

        # Client to authenticate users from pool
        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            user_pool_client_name=f"{project_name}-client",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                callback_urls=[
                    f"https://{dist.domain_name}"
                ],
                logout_urls=[
                    f"https://{dist.domain_name}",
                ],
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
        )


        # DynamoDB (orders)
        table = dynamodb.Table(
            self,
            "OrdersTable",
            table_name=f"{project_name}-orders-db",
            partition_key=dynamodb.Attribute(name="orderId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        table.add_global_secondary_index(
            index_name="UserOrdersIndex",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # Lambda  — one function handles GET and POST
        handler = _lambda.Function(
            self,
            "OrderHandler",
            function_name=f"{project_name}-order-handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambda_code"), # The lambda code from "lambda_code" folder
            handler="order_handler.handler",
            environment={
                "TABLE_NAME": table.table_name,
                "SENDER_EMAIL": "buy-n-track@outlook.com" # SENDER_EMAIL verified and used by SES to send order confirmation emails
            },
            memory_size=128,                                
            timeout=Duration.seconds(5),                   
            log_retention=logs.RetentionDays.ONE_WEEK,     
        )

        # Allows Lambda to send emails using SES
        handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )
        table.grant_read_write_data(handler)

        # API Gateway (REST) 
        api = apigw.RestApi(
            self,
            "OrderApi",
            rest_api_name=f"{project_name}-api",
            deploy_options=apigw.StageOptions(stage_name="prod"),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=apigw.Cors.DEFAULT_HEADERS,
            ),
        )

        # Cognito auth for API Access
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "ApiAuth",
            cognito_user_pools=[user_pool],
        )

        order = api.root.add_resource("order")
        integration = apigw.LambdaIntegration(handler)
        order.add_method("POST", integration,
                         authorization_type=apigw.AuthorizationType.COGNITO,
                         authorizer=authorizer) # POST /order
        order.add_method("GET", integration,
                         authorization_type=apigw.AuthorizationType.COGNITO,
                         authorizer=authorizer) # GET /order
        order_by_id = order.add_resource("{id}") # GET /order/{id}
        order_by_id.add_method("GET", integration,
                         authorization_type=apigw.AuthorizationType.COGNITO,
                         authorizer=authorizer)

        # Store static web files into S3
        deploy_site = s3deploy.BucketDeployment(
            self,
            "OrderFrontendDeplotment",
            destination_bucket=site_bucket,
            sources=[s3deploy.Source.asset("./web/dist")],
            destination_key_prefix="",
            prune=False,
            retain_on_delete=False,
        )

        # Write config.json with the real API URL at deploy time & user credentials
        config_key = "config.json"
        config_body = (
            '{'
            f'"apiBase":"{api.url}order",'
            f'"region":"us-east-1",'
            f'"userPoolId":"{user_pool.user_pool_id}",'
            f'"userPoolClientId":"{user_pool_client.user_pool_client_id}",'
            f'"cognitoDomain":"https://{project_name}.auth.us-east-1.amazoncognito.com"'
            '}'
        )

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

        # Metrics Cloudwatch dashboard setup
        dashboard = cloudwatch.Dashboard(self, "OrderTrackerDashboard",
                                         dashboard_name=f"{project_name}-dashboard")

        dashboard.add_widgets(
            cloudwatch.GraphWidget(title="Lambda Order Handler Invocations", left=[handler.metric_invocations()]),
            cloudwatch.GraphWidget(title="Lambda Order Handler Duration", left=[handler.metric_duration()]),
            cloudwatch.GraphWidget(title="Lambda Order Handler Errors", left=[handler.metric_errors()]),
            cloudwatch.GraphWidget(title="API Gateway Server (5XX) Errors", left=[api.metric_server_error()]),
            cloudwatch.GraphWidget(title="API Gateway Client (4XX) Errors", left=[api.metric_client_error()])
        )

        # Outputs
        CfnOutput(self, "ApiEndpoint", value=api.url)
        CfnOutput(self, "TableName", value=table.table_name)
        CfnOutput(self, "FunctionName", value=handler.function_name)
        CfnOutput(self, "CloudFrontURL", value=f"https://{dist.domain_name}")
        CfnOutput(self, "ConfigURL", value=f"https://{dist.domain_name}/config.json")
