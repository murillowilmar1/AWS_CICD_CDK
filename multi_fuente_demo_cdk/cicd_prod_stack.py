from constructs import Construct
from aws_cdk import Stack, aws_codestarconnections as codestarconnections

from multi_fuente_demo_cdk.constructs.promote_pipeline import PromotePipeline

GITHUB_OWNER = "murillowilmar1"
GITHUB_REPO = "AWS_CICD_CDK"
PROD_BRANCH = "main"


class CicdProdStack(Stack):
    """Un unico pipeline parametrico (pipeline variable FUENTE), sin
    trigger automatico, con aprobacion manual antes de aplicar.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Recurso regional: se declara en este stack para que quede en la
        # misma region que el pipeline de prod (us-west-2).
        github_connection = codestarconnections.CfnConnection(
            self, "GitHubConnection",
            connection_name="multi-fuente-demo-github-prod",
            provider_type="GitHub",
        )

        self.promote_pipeline = PromotePipeline(
            self, "PromotePipeline",
            connection_arn=github_connection.attr_connection_arn,
            owner=GITHUB_OWNER,
            repo=GITHUB_REPO,
            branch=PROD_BRANCH,
        )
