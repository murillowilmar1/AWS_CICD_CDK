from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_iam as iam,
)

PLAN_BUILDSPEC = {
    "version": "0.2",
    "phases": {
        "install": {
            "runtime-versions": {"python": "3.12"},
            "commands": ["npm install -g aws-cdk", "pip install -r requirements.txt"],
        },
        "build": {
            "commands": [
                'STACK_NAME="Fuente${FUENTE^}-Prod"',
                "echo Sintetizando $STACK_NAME (FUENTE=$FUENTE)",
                'cdk synth "$STACK_NAME" --quiet',
            ],
        },
    },
    "artifacts": {
        "base-directory": "cdk.out",
        "files": ["**/*"],
    },
}

APPLY_BUILDSPEC = {
    "version": "0.2",
    "phases": {
        "install": {
            "runtime-versions": {"python": "3.12"},
            "commands": ["npm install -g aws-cdk", "pip install -r requirements.txt"],
        },
        "build": {
            "commands": [
                'STACK_NAME="Fuente${FUENTE^}-Prod"',
                "echo Aplicando $STACK_NAME (FUENTE=$FUENTE)",
                'cdk deploy "$STACK_NAME" --app "$CODEBUILD_SRC_DIR_PlanOutput" --require-approval never',
            ],
        },
    },
}


class PromotePipeline(Construct):
    """Pipeline parametrico de prod: una unica pipeline (no una por
    fuente) que se arranca a mano con la pipeline variable FUENTE
    (postgres|sqlserver). No se dispara con push (el trigger apunta a
    una ruta que nunca existe, a proposito). Aprobacion manual antes
    de Apply.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        connection_arn: str,
        owner: str,
        repo: str,
        branch: str = "main",
        build_image: codebuild.IBuildImage = codebuild.LinuxBuildImage.STANDARD_7_0,
    ) -> None:
        super().__init__(scope, construct_id)

        account = Stack.of(self).account
        assume_cdk_roles = iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            resources=[f"arn:aws:iam::{account}:role/cdk-*"],
        )

        fuente_var = codepipeline.Variable(
            variable_name="FUENTE",
            default_value="postgres",
            description="Fuente a promover a prod: postgres | sqlserver",
        )

        source_output = codepipeline.Artifact("SourceOutput")
        plan_output = codepipeline.Artifact("PlanOutput")

        source_action = cpactions.CodeStarConnectionsSourceAction(
            action_name="Source",
            connection_arn=connection_arn,
            owner=owner,
            repo=repo,
            branch=branch,
            output=source_output,
            trigger_on_push=False,
        )

        fuente_env_var = {
            "FUENTE": codebuild.BuildEnvironmentVariable(value=fuente_var.reference()),
        }

        plan_project = codebuild.PipelineProject(
            self, "PlanProject",
            project_name="promote-plan-prod",
            build_spec=codebuild.BuildSpec.from_object(PLAN_BUILDSPEC),
            environment=codebuild.BuildEnvironment(build_image=build_image),
        )
        plan_project.add_to_role_policy(assume_cdk_roles)

        apply_project = codebuild.PipelineProject(
            self, "ApplyProject",
            project_name="promote-apply-prod",
            build_spec=codebuild.BuildSpec.from_object(APPLY_BUILDSPEC),
            environment=codebuild.BuildEnvironment(build_image=build_image),
        )
        apply_project.add_to_role_policy(assume_cdk_roles)

        plan_action = cpactions.CodeBuildAction(
            action_name="Plan",
            project=plan_project,
            input=source_output,
            outputs=[plan_output],
            environment_variables=fuente_env_var,
        )

        approval_action = cpactions.ManualApprovalAction(
            action_name="ApproveApply",
        )

        apply_action = cpactions.CodeBuildAction(
            action_name="Apply",
            project=apply_project,
            input=source_output,
            extra_inputs=[plan_output],
            environment_variables=fuente_env_var,
        )

        self.pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name="promote-prod",
            pipeline_type=codepipeline.PipelineType.V2,
            variables=[fuente_var],
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[source_action]),
                codepipeline.StageProps(stage_name="Build", actions=[plan_action]),
                codepipeline.StageProps(stage_name="Approval", actions=[approval_action]),
                codepipeline.StageProps(stage_name="Apply", actions=[apply_action]),
            ],
            triggers=[
                # Ruta que nunca existe: el push a `branch` nunca dispara
                # este pipeline. Se arranca a mano con --variables name=FUENTE,value=...
                codepipeline.TriggerProps(
                    provider_type=codepipeline.ProviderType.CODE_STAR_SOURCE_CONNECTION,
                    git_configuration=codepipeline.GitConfiguration(
                        source_action=source_action,
                        push_filter=[
                            codepipeline.GitPushFilter(
                                branches_includes=[branch],
                                file_paths_includes=["__never_triggers__/**"],
                            ),
                        ],
                    ),
                ),
            ],
        )
