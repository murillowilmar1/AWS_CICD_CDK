from typing import Dict, Optional

from constructs import Construct
from aws_cdk import Duration, aws_iam as iam, aws_lambda as _lambda


class LambdaFunctionConstruct(Construct):
    """Construct reutilizable para una funcion Lambda."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        function_name: str,
        code_path: str,
        handler: str,
        role: iam.IRole,
        environment: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 60,
        memory_size: int = 256,
        runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_12,
    ) -> None:
        super().__init__(scope, construct_id)

        self.function = _lambda.Function(
            self, "Function",
            function_name=function_name,
            runtime=runtime,
            handler=handler,
            code=_lambda.Code.from_asset(code_path),
            role=role,
            environment=environment or {},
            timeout=Duration.seconds(timeout_seconds),
            memory_size=memory_size,
        )
