from constructs import Construct
from aws_cdk import Stack


class CicdProdStack(Stack):
    """Un unico pipeline parametrico (pipeline variable FUENTE), sin
    trigger automatico, con aprobacion manual antes de aplicar.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: PromotePipeline construct (variable FUENTE, approval manual)
