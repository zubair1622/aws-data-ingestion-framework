import sys
import boto3
import os

from awsglue.context import GlueContext
from pyspark.context import SparkContext

# Initialize Spark and Glue contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# S3 Setup
input_bucket = "datascience-input100"
output_bucket = "datascience-output100"

temp_prefix = "temp/"

# S3 client
s3 = boto3.client("s3")

# Scan entire bucket
response = s3.list_objects_v2(Bucket=input_bucket)

csv_files = [

    obj["Key"]

    for obj in response.get("Contents", [])

    if obj["Key"].endswith(".csv")

]

for key in csv_files:

    print(f"Processing : {key}")

    # Example:
    # customers/Delta_load/csv_files/2026/Mar/31/Customers.csv

    path_parts = key.split("/")

    # Skip invalid structures
    if len(path_parts) < 7:
        continue

    entity_name = path_parts[0]
    load_type = path_parts[1]
    file_folder = path_parts[2]

    year = path_parts[3]
    month = path_parts[4]
    day = path_parts[5]

    filename = path_parts[6]

    base_name = filename.replace(".csv", "")

    input_path = f"s3://{input_bucket}/{key}"

    # NEW OUTPUT STRUCTURE
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

    print(f"Output : {final_parquet_key}")

    # Read CSV
    df = (
        spark.read
        .option("header", True)
        .csv(input_path)
    )

    # Write temporary parquet
    df.coalesce(1) \
      .write \
      .mode("overwrite") \
      .parquet(temp_output_path)

    # Find parquet file
    temp_objects = s3.list_objects_v2(
        Bucket=output_bucket,
        Prefix=f"{temp_prefix}{base_name}/"
    )

    parquet_key = None

    for obj in temp_objects.get("Contents", []):

        if obj["Key"].endswith(".parquet"):

            parquet_key = obj["Key"]
            break

    # Copy parquet to final location
    if parquet_key:

        s3.copy_object(
            Bucket=output_bucket,
            CopySource={
                "Bucket": output_bucket,
                "Key": parquet_key
            },
            Key=final_parquet_key
        )

    # Cleanup temp files
    for obj in temp_objects.get("Contents", []):

        s3.delete_object(
            Bucket=output_bucket,
            Key=obj["Key"]
        )

print(
    "✅ All CSV files converted to Parquet and saved with original filenames."
)

