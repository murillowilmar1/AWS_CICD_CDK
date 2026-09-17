from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_iam as iam,
)


class SourcePipeline(Construct):
    """Pipeline por fuente (dev): Source -> Build/plan -> Apply.

    Se dispara solo cuando un push a `branch` toca `fuente_path` (path
    filter via trigger.gitConfiguration.pushFilter). Sin aprobacion manual.

    El stage de plan corre `cdk synth` y publica el cloud assembly
    (`cdk.out`) como artifact; el stage de apply recibe DOS input
    artifacts -- el repo completo (fuente primaria) y ese cloud assembly
    (fuente secundaria) -- y corre `cdk deploy --app <cloud-assembly>`
    para desplegar exactamente lo que se sintetizo en el plan.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        source_name: str,
        env_name: str,
        connection_arn: str,
        owner: str,
        repo: str,
        branch: str,
        fuente_path: str,
        build_image: codebuild.IBuildImage = codebuild.LinuxBuildImage.STANDARD_7_0,
    ) -> None:
        super().__init__(scope, construct_id)

        account = Stack.of(self).account
        assume_cdk_roles = iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            resources=[f"arn:aws:iam::{account}:role/cdk-*"],
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
            trigger_on_push=False,  # el trigger real es el path filter de mas abajo
        )

        plan_project = codebuild.PipelineProject(
            self, "PlanProject",
            project_name=f"{source_name}-plan-{env_name}",
            build_spec=codebuild.BuildSpec.from_source_filename(f"{fuente_path}/buildspec.yml"),
            environment=codebuild.BuildEnvironment(build_image=build_image),
        )
        plan_project.add_to_role_policy(assume_cdk_roles)

        apply_project = codebuild.PipelineProject(
            self, "ApplyProject",
            project_name=f"{source_name}-apply-{env_name}",
            build_spec=codebuild.BuildSpec.from_source_filename(f"{fuente_path}/buildspec-apply.yml"),
            environment=codebuild.BuildEnvironment(build_image=build_image),
        )
        apply_project.add_to_role_policy(assume_cdk_roles)

        plan_action = cpactions.CodeBuildAction(
            action_name="Plan",
            project=plan_project,
            input=source_output,
            outputs=[plan_output],
        )

        apply_action = cpactions.CodeBuildAction(
            action_name="Apply",
            project=apply_project,
            input=source_output,
            extra_inputs=[plan_output],
        )

        self.pipeline = codepipeline.Pipeline(
            self, "Pipeline",
            pipeline_name=f"{source_name}-{env_name}",
            pipeline_type=codepipeline.PipelineType.V2,
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[source_action]),
                codepipeline.StageProps(stage_name="Build", actions=[plan_action]),
                codepipeline.StageProps(stage_name="Apply", actions=[apply_action]),
            ],
            triggers=[
                codepipeline.TriggerProps(
                    provider_type=codepipeline.ProviderType.CODE_STAR_SOURCE_CONNECTION,
                    git_configuration=codepipeline.GitConfiguration(
                        source_action=source_action,
                        push_filter=[
                            codepipeline.GitPushFilter(
                                branches_includes=[branch],
                                file_paths_includes=[f"{fuente_path}/**"],
                            ),
                        ],
                    ),
                ),
            ],
        )
