from constructs import Construct


class SourcePipeline(Construct):
    """Pipeline por fuente: Source -> Build/plan -> [Approval opcional] -> Apply.

    Se dispara solo cuando el push toca la carpeta de la fuente
    (path filter via trigger.gitConfiguration.pushFilter).
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        # TODO: CodePipeline (PipelineType.V2) con trigger de path filter
        # TODO: CodeBuild project de plan
        # TODO: CodeBuild project de apply (dos input artifacts, PrimarySource)
