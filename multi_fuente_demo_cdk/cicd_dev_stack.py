from constructs import Construct
from aws_cdk import Stack, aws_codestarconnections as codestarconnections

from multi_fuente_demo_cdk.constructs.source_pipeline import SourcePipeline

GITHUB_OWNER = "murillowilmar1"
GITHUB_REPO = "AWS_CICD_CDK"
DEV_BRANCH = "dev"


class CicdDevStack(Stack):
    """Un pipeline de CodePipeline por fuente (postgres, sqlserver),
    disparado solo cuando el push a `dev` toca la carpeta de esa fuente,
    sin aprobacion manual.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # La conexion es un recurso regional: se declara aqui para que se
        # cree en la misma region que este stack/pipeline (los source
        # actions de CodePipeline no soportan referencias cross-region).
        github_connection = codestarconnections.CfnConnection(
            self, "GitHubConnection",
            connection_name="multi-fuente-demo-github-dev",
            provider_type="GitHub",
        )

        self.postgres_pipeline = SourcePipeline(
            self, "PostgresPipeline",
            source_name="postgres",
            env_name="dev",
            connection_arn=github_connection.attr_connection_arn,
            owner=GITHUB_OWNER,
            repo=GITHUB_REPO,
            branch=DEV_BRANCH,
            fuente_path="fuentes/fuente_postgres",
        )

        self.sqlserver_pipeline = SourcePipeline(
            self, "SqlserverPipeline",
            source_name="sqlserver",
            env_name="dev",
            connection_arn=github_connection.attr_connection_arn,
            owner=GITHUB_OWNER,
            repo=GITHUB_REPO,
            branch=DEV_BRANCH,
            fuente_path="fuentes/fuente_sqlserver",
        )
