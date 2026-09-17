from pathlib import Path

from constructs import Construct
from aws_cdk import Stack, aws_iam as iam, aws_s3 as s3

from multi_fuente_demo_cdk.constructs.glue_job_construct import GlueJobConstruct

SOURCE_NAME = "postgres"
SRC_DIR = Path(__file__).parent / "src"


class FuentePostgresInfraStack(Stack):
    """3 Glue Jobs (raw -> stage -> analytics) para la fuente postgres.

    Consume los buckets/rol/catalogo compartidos de PlatformSharedStack;
    cada job escribe bajo el prefijo `postgres/` de cada bucket.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_name: str,
        raw_bucket: s3.IBucket,
        stage_bucket: s3.IBucket,
        analytics_bucket: s3.IBucket,
        glue_job_role: iam.IRole,
        glue_database_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        common_arguments = {
            "--job-bookmark-option": "job-bookmark-enable",
            "--enable-metrics": "true",
            "--enable-continuous-cloudwatch-log": "true",
            "--enable-glue-datacatalog": "true",
            "--TempDir": f"s3://{stage_bucket.bucket_name}/tmp/{SOURCE_NAME}/",
            "--RAW_BUCKET": raw_bucket.bucket_name,
            "--STAGE_BUCKET": stage_bucket.bucket_name,
            "--ANALYTICS_BUCKET": analytics_bucket.bucket_name,
            "--SOURCE_PREFIX": SOURCE_NAME,
            "--GLUE_DATABASE": glue_database_name,
        }

        self.raw_job = GlueJobConstruct(
            self, "RawJob",
            job_name=f"{SOURCE_NAME}-raw-{env_name}",
            script_path=str(SRC_DIR / "raw" / "job.py"),
            role=glue_job_role,
            default_arguments={
                **common_arguments,
                # --CONNECTION_NAME / --SOURCE_TABLE se resuelven por tabla en runtime.
            },
        )

        self.stage_job = GlueJobConstruct(
            self, "StageJob",
            job_name=f"{SOURCE_NAME}-stage-{env_name}",
            script_path=str(SRC_DIR / "stage" / "job.py"),
            role=glue_job_role,
            default_arguments=common_arguments,
        )

        self.analytics_job = GlueJobConstruct(
            self, "AnalyticsJob",
            job_name=f"{SOURCE_NAME}-analytics-{env_name}",
            script_path=str(SRC_DIR / "analytics" / "job.py"),
            role=glue_job_role,
            default_arguments=common_arguments,
        )
