# multi-fuente-demo (AWS CDK / Python)

Equivalente en AWS CDK (Python) del laboratorio de CI/CD multi-fuente
originalmente implementado en Terraform.

## Arquitectura

- `multi_fuente_demo_cdk/platform_shared_stack.py` — capa compartida por
  todas las fuentes: buckets S3 raw/stage/analytics, Glue Catalog Database,
  Athena Workgroup y roles IAM compartidos. Un stack por ambiente
  (dev/prod).
- `multi_fuente_demo_cdk/cicd_dev_stack.py` — un pipeline de CodePipeline
  por fuente, disparado solo cuando el push toca la carpeta de esa
  fuente (path filter), sin aprobación manual.
- `multi_fuente_demo_cdk/cicd_prod_stack.py` — un único pipeline
  paramétrico (pipeline variable `FUENTE`), sin trigger automático,
  arrancado a mano, con aprobación manual antes de aplicar.
- `multi_fuente_demo_cdk/constructs/` — constructs reutilizables
  (pipeline por fuente, pipeline paramétrico de prod, Glue Job, Lambda).
- `fuentes/fuente_postgres/`, `fuentes/fuente_sqlserver/` — stack de
  infraestructura por fuente (Glue Jobs raw/stage/analytics; SQL Server
  además incluye una Lambda de auditoría), scripts de los jobs y
  buildspecs de CodeBuild.

Dev y prod se despliegan en la misma cuenta de AWS, en regiones
distintas.

## Requisitos previos

```
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt -r requirements-dev.txt
```

`cdk bootstrap` debe ejecutarse una vez por cada combinación de
cuenta+región usada (dev y prod):

```
cdk bootstrap aws://ACCOUNT_ID/REGION_DEV
cdk bootstrap aws://ACCOUNT_ID/REGION_PROD
```

## Comandos útiles

- `cdk synth` — sintetiza el CloudFormation de todos los stacks
- `cdk diff` — compara el stack desplegado con el estado actual
- `cdk deploy <StackName>` — despliega un stack
- `pytest` — corre los tests unitarios (`tests/unit`)

## Promoción de una fuente a prod

Antes de promover una fuente, se sincroniza `main` con un merge acotado
a la carpeta de esa fuente únicamente:

```
git checkout main
git checkout dev -- fuentes/fuente_postgres
git commit -m "promote: fuente_postgres a prod"
```

Nunca se hace merge completo de `dev`.

Para arrancar el pipeline paramétrico de prod indicando la fuente:

```
aws codepipeline start-pipeline-execution \
  --name <nombre-del-pipeline-prod> \
  --variables name=FUENTE,value=postgres
```
