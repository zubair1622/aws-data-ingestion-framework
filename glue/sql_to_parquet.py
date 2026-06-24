import sys
import boto3
import os
import re
from datetime import datetime
from pyspark.sql import Row
from pyspark.context import SparkContext
from awsglue.context import GlueContext

# Init Spark/Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Date structure
today = datetime.today()
year = today.strftime("%Y")
month = today.strftime("%b")
day = today.strftime("%d")

# S3 paths
input_bucket = "datascience-input-bucket"
output_bucket = "datascience-output-bucket"
input_prefix = f"sql_files/Full_load/{year}/{month}/{day}/"
output_prefix = f"bronze/sql/{year}/{month}/{day}/"
temp_prefix = f"temp/"

s3 = boto3.client("s3")

# List .sql files
response = s3.list_objects_v2(Bucket=input_bucket, Prefix=input_prefix)
sql_files = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".sql")]

for key in sql_files:
    filename = os.path.basename(key)
    base_name = filename.replace(".sql", "")
    input_path = f"s3://{input_bucket}/{key}"
    temp_output_path = f"s3://{output_bucket}/{temp_prefix}{base_name}/"
    final_parquet_key = f"{output_prefix}{base_name}.parquet"

    # Load file content
    obj = s3.get_object(Bucket=input_bucket, Key=key)
    raw_sql = obj["Body"].read().decode("utf-8")

    # Extract all INSERT statements
    insert_lines = [line.strip() for line in raw_sql.splitlines() if line.upper().startswith("INSERT INTO")]

    # Extract column names from first insert
    first_insert = insert_lines[0]
    match = re.search(r"\((.*?)\)\s+VALUES", first_insert, re.IGNORECASE)
    columns = [col.strip() for col in match.group(1).split(",")]

    # Extract values from all insert lines
    values = []
    for line in insert_lines:
        val_match = re.search(r"VALUES\s*\((.*?)\);?$", line, re.IGNORECASE)
        if val_match:
            raw_vals = val_match.group(1)
            parsed_vals = []
            for val in re.split(r",(?![^']*')", raw_vals):  # split on commas outside quotes
                val = val.strip().strip("'")
                parsed_vals.append(val)
            values.append(parsed_vals)

    # Convert to DataFrame
    rows = [Row(**dict(zip(columns, vals))) for vals in values]
    df = spark.createDataFrame(rows)

    # Write Parquet
    df.coalesce(1).write.mode("overwrite").parquet(temp_output_path)

    # Rename to original file name
    temp_objects = s3.list_objects_v2(Bucket=output_bucket, Prefix=f"{temp_prefix}{base_name}/")
    parquet_key = next((obj["Key"] for obj in temp_objects.get("Contents", []) if obj["Key"].endswith(".parquet")), None)

    if parquet_key:
        s3.copy_object(
            Bucket=output_bucket,
            CopySource={"Bucket": output_bucket, "Key": parquet_key},
            Key=final_parquet_key
        )

    # Clean up temp files
    for obj in temp_objects.get("Contents", []):
        s3.delete_object(Bucket=output_bucket, Key=obj["Key"])

print("✅ SQL file parsed and saved as Parquet.")

