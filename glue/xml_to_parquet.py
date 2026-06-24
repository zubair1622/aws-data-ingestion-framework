import sys
import boto3
import os
from datetime import datetime
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
# Initialize Spark and Glue contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
# Date for folder structure
today = datetime.today()
year = today.strftime("%Y")
month = today.strftime("%b")
day = today.strftime("%d")
# S3 Setup
input_bucket = "datascience-input-bucket"
output_bucket = "datascience-output-bucket"
input_prefix = f"xml_files/Full_load/{year}/{month}/{day}/"
output_prefix = f"bronze/{year}/{month}/{day}/"
temp_prefix = f"temp/"
# S3 client
s3 = boto3.client('s3')
# List XML files in input path
response = s3.list_objects_v2(Bucket=input_bucket, Prefix=input_prefix)
xml_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith(".xml")]
for key in xml_files:
    filename = os.path.basename(key)                    
    base_name = filename.replace(".xml", "")            
    input_path = f"s3://{input_bucket}/{key}"
    temp_output_path = f"s3://{output_bucket}/{temp_prefix}{base_name}/"
    final_parquet_key = f"{output_prefix}{base_name}.parquet"
    # ✅ Read XML using Spark XML with rowTag = "row"
    df = spark.read \
        .format("com.databricks.spark.xml") \
        .option("rowTag", "row") \
        .load(input_path)
    # Write as single Parquet file to temp location
    df.coalesce(1).write.mode("overwrite").parquet(temp_output_path)
    # Find the .parquet file in temp location
    temp_objects = s3.list_objects_v2(Bucket=output_bucket, Prefix=f"{temp_prefix}{base_name}/")
    parquet_key = None
    for obj in temp_objects.get("Contents", []):
        if obj["Key"].endswith(".parquet"):
            parquet_key = obj["Key"]
            break
    # Copy to final destination with original filename
    if parquet_key:
        s3.copy_object(
            Bucket=output_bucket,
            CopySource={"Bucket": output_bucket, "Key": parquet_key},
            Key=final_parquet_key
        )
    # Clean up temp directory
    for obj in temp_objects.get("Contents", []):
        s3.delete_object(Bucket=output_bucket, Key=obj["Key"])

print("✅ All XML files converted to Parquet and saved with original filenames.")

