import sys
import boto3
import os

from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext

# Initialize Spark
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Read S3 key passed by Lambda
args = getResolvedOptions(
    sys.argv,
    ['s3_key']
)

key = args['s3_key']

# Buckets
input_bucket = "datascience-input100"
output_bucket = "datascience-output100"

temp_prefix = "temp/"

s3 = boto3.client("s3")

print(f"Processing file : {key}")

# Example:
# customers/Delta_load/csv_files/2026/Mar/31/Customers.csv

path_parts = key.split("/")

if len(path_parts) < 7:
    raise Exception(
        f"Invalid folder structure : {key}"
    )

entity_name = path_parts[0]
load_type = path_parts[1]
file_folder = path_parts[2]

year = path_parts[3]
month = path_parts[4]
day = path_parts[5]

filename = path_parts[6]

base_name = filename.replace(".csv", "")

input_path = (
    f"s3://{input_bucket}/{key}"
)

output_prefix = (
    f"bronze/"
    f"{entity_name}/"
    f"{load_type}/"
    f"{file_folder}/"
    f"{year}/"
    f"{month}/"
    f"{day}/"
)

temp_output_path = (
    f"s3://{output_bucket}/"
    f"{temp_prefix}{base_name}/"
)

final_parquet_key = (
    f"{output_prefix}"
    f"{base_name}.parquet"
)

print(
    f"Writing To : "
    f"{final_parquet_key}"
)

# Read CSV

df = (
    spark.read
    .option("header", True)
    .csv(input_path)
)

# Write temp parquet

df.coalesce(1) \
  .write \
  .mode("overwrite") \
  .parquet(temp_output_path)

# Locate generated parquet

temp_objects = s3.list_objects_v2(
    Bucket=output_bucket,
    Prefix=f"{temp_prefix}{base_name}/"
)

parquet_key = None

for obj in temp_objects.get("Contents", []):

    if obj["Key"].endswith(".parquet"):

        parquet_key = obj["Key"]
        break

# Copy to final location

if parquet_key:

    s3.copy_object(
        Bucket=output_bucket,
        CopySource={
            "Bucket": output_bucket,
            "Key": parquet_key
        },
        Key=final_parquet_key
    )

# Cleanup temp folder

for obj in temp_objects.get("Contents", []):

    s3.delete_object(
        Bucket=output_bucket,
        Key=obj["Key"]
    )

print(
    f"Completed : {filename}"
)

