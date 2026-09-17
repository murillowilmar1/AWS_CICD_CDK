from constructs import Construct
from aws_cdk import Stack


class CicdDevStack(Stack):
    """Un pipeline de CodePipeline por fuente (postgres, sqlserver),
    disparado solo cuando el push toca la carpeta de esa fuente,
    sin aprobacion manual.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: SourcePipeline construct para fuente_postgres
        # TODO: SourcePipeline construct para fuente_sqlserver
