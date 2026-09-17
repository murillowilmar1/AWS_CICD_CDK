from constructs import Construct
from aws_cdk import (
    Stack,
    Tags,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_glue as glue,
    aws_athena as athena,
)


class PlatformSharedStack(Stack):
    """Capa compartida por todas las fuentes: buckets raw/stage/analytics,
    Glue Catalog Database, Athena Workgroup y roles IAM compartidos.

    Un solo bucket por capa (raw/stage/analytics) para todas las fuentes;
    cada fuente escribe bajo su propio prefijo dentro de cada bucket.
    """

    def __init__(self, scope: Construct, construct_id: str, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        database_name = f"multi_fuente_{env_name}"

        # Lab/dev se puede destruir libremente; prod se retiene por seguridad.
        removal_policy = RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN
        auto_delete_objects = env_name == "dev"

        # --- Buckets S3 compartidos (raw / stage / analytics) ---
        bucket_kwargs = dict(
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=removal_policy,
            auto_delete_objects=auto_delete_objects,
        )

        self.raw_bucket = s3.Bucket(
            self, "RawBucket",
            bucket_name=f"multi-fuente-{env_name}-raw-{self.account}-{self.region}",
            **bucket_kwargs,
        )
        self.stage_bucket = s3.Bucket(
            self, "StageBucket",
            bucket_name=f"multi-fuente-{env_name}-stage-{self.account}-{self.region}",
            **bucket_kwargs,
        )
        self.analytics_bucket = s3.Bucket(
            self, "AnalyticsBucket",
            bucket_name=f"multi-fuente-{env_name}-analytics-{self.account}-{self.region}",
            **bucket_kwargs,
        )

        # --- Glue Catalog Database (unica, compartida por todas las fuentes) ---
        self.glue_database = glue.CfnDatabase(
            self, "GlueCatalogDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=database_name,
                description="Catalogo compartido por todas las fuentes de datos",
            ),
        )
        self.glue_database_name = database_name

        # --- Athena Workgroup (unico, resultados en el bucket analytics) ---
        self.athena_workgroup = athena.CfnWorkGroup(
            self, "AthenaWorkgroup",
            name=f"multi-fuente-{env_name}",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.analytics_bucket.bucket_name}/athena-results/",
                ),
                enforce_work_group_configuration=True,
                publish_cloud_watch_metrics_enabled=True,
            ),
        )

        # --- Rol IAM compartido: ejecucion de Glue Jobs (todas las fuentes) ---
        self.glue_job_role = iam.Role(
            self, "GlueJobRole",
            role_name=f"multi-fuente-{env_name}-glue-job-role",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
            ],
        )
        for bucket in (self.raw_bucket, self.stage_bucket, self.analytics_bucket):
            bucket.grant_read_write(self.glue_job_role)

        self.glue_job_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "glue:GetDatabase",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:CreateTable",
                    "glue:UpdateTable",
                    "glue:GetPartition",
                    "glue:GetPartitions",
                    "glue:CreatePartition",
                    "glue:BatchCreatePartition",
                ],
                resources=[
                    f"arn:aws:glue:{self.region}:{self.account}:catalog",
                    f"arn:aws:glue:{self.region}:{self.account}:database/{database_name}",
                    f"arn:aws:glue:{self.region}:{self.account}:table/{database_name}/*",
                ],
            )
        )

        # --- Rol IAM compartido: Lambdas de auditoria (ej. fuente_sqlserver) ---
        self.lambda_execution_role = iam.Role(
            self, "LambdaAuditRole",
            role_name=f"multi-fuente-{env_name}-lambda-audit-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )
        for bucket in (self.raw_bucket, self.stage_bucket):
            bucket.grant_read(self.lambda_execution_role)
        # La auditoria escribe sus registros bajo el prefijo audit/ del bucket analytics.
        self.analytics_bucket.grant_read_write(self.lambda_execution_role)

        Tags.of(self).add("Project", "multi-fuente-demo")
        Tags.of(self).add("Environment", env_name)
