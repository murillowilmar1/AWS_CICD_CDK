from constructs import Construct


class PromotePipeline(Construct):
    """Pipeline parametrico de prod: pipeline variable FUENTE, trigger
    apuntando a una ruta que nunca existe (sin disparo automatico),
    aprobacion manual antes de Apply.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        # TODO: codepipeline.Variable(variable_name="FUENTE")
        # TODO: CodeBuild plan usando #{variables.FUENTE} / variable.reference()
        # TODO: ManualApprovalAction
        # TODO: CodeBuild apply (dos input artifacts, PrimarySource)
