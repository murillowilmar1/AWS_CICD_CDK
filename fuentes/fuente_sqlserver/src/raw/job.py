import sys

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "RAW_BUCKET", "SOURCE_PREFIX", "CONNECTION_NAME", "SOURCE_TABLE"],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# TODO: reemplazar por la conexion JDBC real hacia SQL Server (Glue Connection).
source_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="sqlserver",
    connection_options={
        "useConnectionProperties": "true",
        "connectionName": args["CONNECTION_NAME"],
        "dbtable": args["SOURCE_TABLE"],
    },
    transformation_ctx="source_dyf",
)

output_path = f"s3://{args['RAW_BUCKET']}/{args['SOURCE_PREFIX']}/{args['SOURCE_TABLE']}/"

glueContext.write_dynamic_frame.from_options(
    frame=source_dyf,
    connection_type="s3",
    connection_options={"path": output_path},
    format="parquet",
    transformation_ctx="raw_sink",
)

job.commit()
