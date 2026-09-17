import sys

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "STAGE_BUCKET", "ANALYTICS_BUCKET", "SOURCE_PREFIX", "GLUE_DATABASE"],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

stage_path = f"s3://{args['STAGE_BUCKET']}/{args['SOURCE_PREFIX']}/"

stage_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [stage_path], "recurse": True},
    format="parquet",
    transformation_ctx="stage_dyf",
)

# TODO: agregaciones/joins reales de la capa analytics por fuente.
analytics_dyf = stage_dyf

analytics_path = f"s3://{args['ANALYTICS_BUCKET']}/{args['SOURCE_PREFIX']}/"
table_name = f"{args['SOURCE_PREFIX']}_analytics"

sink = glueContext.getSink(
    connection_type="s3",
    path=analytics_path,
    enableUpdateCatalog=True,
    updateBehavior="UPDATE_IN_DATABASE",
    transformation_ctx="analytics_sink",
)
sink.setFormat("glueparquet")
sink.setCatalogInfo(catalogDatabase=args["GLUE_DATABASE"], catalogTableName=table_name)
sink.writeFrame(analytics_dyf)

job.commit()
