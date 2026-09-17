#!/usr/bin/env python3
import os

import aws_cdk as cdk

from multi_fuente_demo_cdk.platform_shared_stack import PlatformSharedStack
from multi_fuente_demo_cdk.cicd_dev_stack import CicdDevStack
from multi_fuente_demo_cdk.cicd_prod_stack import CicdProdStack
from fuentes.fuente_postgres.infra_stack import FuentePostgresInfraStack
from fuentes.fuente_sqlserver.infra_stack import FuenteSqlserverInfraStack

app = cdk.App()

account = os.getenv("CDK_DEFAULT_ACCOUNT")

# Mismo account, una region por ambiente (equivalente a la topologia de Terraform).
dev_env = cdk.Environment(account=account, region=app.node.try_get_context("dev_region") or "us-east-1")
prod_env = cdk.Environment(account=account, region=app.node.try_get_context("prod_region") or "us-west-2")

platform_dev = PlatformSharedStack(app, "PlatformShared-Dev", env_name="dev", env=dev_env)
CicdDevStack(app, "Cicd-Dev", env=dev_env)

platform_prod = PlatformSharedStack(app, "PlatformShared-Prod", env_name="prod", env=prod_env)
CicdProdStack(app, "Cicd-Prod", env=prod_env)

FuentePostgresInfraStack(
    app, "FuentePostgres-Dev",
    env_name="dev",
    raw_bucket=platform_dev.raw_bucket,
    stage_bucket=platform_dev.stage_bucket,
    analytics_bucket=platform_dev.analytics_bucket,
    glue_job_role=platform_dev.glue_job_role,
    glue_database_name=platform_dev.glue_database_name,
    env=dev_env,
)

FuentePostgresInfraStack(
    app, "FuentePostgres-Prod",
    env_name="prod",
    raw_bucket=platform_prod.raw_bucket,
    stage_bucket=platform_prod.stage_bucket,
    analytics_bucket=platform_prod.analytics_bucket,
    glue_job_role=platform_prod.glue_job_role,
    glue_database_name=platform_prod.glue_database_name,
    env=prod_env,
)

FuenteSqlserverInfraStack(
    app, "FuenteSqlserver-Dev",
    env_name="dev",
    raw_bucket=platform_dev.raw_bucket,
    stage_bucket=platform_dev.stage_bucket,
    analytics_bucket=platform_dev.analytics_bucket,
    glue_job_role=platform_dev.glue_job_role,
    lambda_execution_role=platform_dev.lambda_execution_role,
    glue_database_name=platform_dev.glue_database_name,
    env=dev_env,
)

FuenteSqlserverInfraStack(
    app, "FuenteSqlserver-Prod",
    env_name="prod",
    raw_bucket=platform_prod.raw_bucket,
    stage_bucket=platform_prod.stage_bucket,
    analytics_bucket=platform_prod.analytics_bucket,
    glue_job_role=platform_prod.glue_job_role,
    lambda_execution_role=platform_prod.lambda_execution_role,
    glue_database_name=platform_prod.glue_database_name,
    env=prod_env,
)

app.synth()
