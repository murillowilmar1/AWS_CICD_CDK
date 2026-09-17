import sys

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "RAW_BUCKET", "STAGE_BUCKET", "SOURCE_PREFIX"],
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

raw_path = f"s3://{args['RAW_BUCKET']}/{args['SOURCE_PREFIX']}/"

raw_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [raw_path], "recurse": True},
    format="parquet",
    transformation_ctx="raw_dyf",
)

# TODO: limpieza/normalizacion real (dedup, tipado, reglas de calidad) por fuente.
stage_df = raw_dyf.toDF().dropDuplicates()

stage_path = f"s3://{args['STAGE_BUCKET']}/{args['SOURCE_PREFIX']}/"
stage_df.write.mode("overwrite").parquet(stage_path)

job.commit()
