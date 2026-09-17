from typing import Dict, List, Optional

from constructs import Construct
from aws_cdk import (
    aws_glue as glue,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
)


class GlueJobConstruct(Construct):
    """Construct reutilizable para un AWS Glue Job (Spark ETL).

    Sube el script local como asset de CDK (se publica en el bucket de
    assets del bootstrap) y le da permiso de lectura al rol de ejecucion.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        job_name: str,
        script_path: str,
        role: iam.IRole,
        default_arguments: Optional[Dict[str, str]] = None,
        connections: Optional[List[str]] = None,
        glue_version: str = "4.0",
        worker_type: str = "G.1X",
        number_of_workers: int = 2,
        timeout_minutes: int = 60,
        max_concurrent_runs: int = 1,
    ) -> None:
        super().__init__(scope, construct_id)

        script_asset = s3_assets.Asset(self, "ScriptAsset", path=script_path)
        script_asset.grant_read(role)

        self.job = glue.CfnJob(
            self, "Job",
            name=job_name,
            role=role.role_arn,
            glue_version=glue_version,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                script_location=script_asset.s3_object_url,
                python_version="3",
            ),
            default_arguments=default_arguments or {},
            worker_type=worker_type,
            number_of_workers=number_of_workers,
            timeout=timeout_minutes,
            execution_property=glue.CfnJob.ExecutionPropertyProperty(
                max_concurrent_runs=max_concurrent_runs,
            ),
            connections=(
                glue.CfnJob.ConnectionsListProperty(connections=connections)
                if connections
                else None
            ),
        )

        self.job_name = job_name
