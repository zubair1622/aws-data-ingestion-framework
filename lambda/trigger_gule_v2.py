import boto3

glue = boto3.client("glue")

GLUE_JOB_NAME = "csv_to_parquet"

def lambda_handler(event, context):

    print(event)

    for record in event["Records"]:

        bucket = (
            record["s3"]["bucket"]["name"]
        )

        s3_key = (
            record["s3"]["object"]["key"]
        )

        print(
            f"Uploaded : "
            f"s3://{bucket}/{s3_key}"
        )

        response = glue.start_job_run(
            JobName=GLUE_JOB_NAME,
            Arguments={
                '--s3_key': s3_key
            }
        )

        print(
            f"Started : "
            f"{response['JobRunId']}"
        )

    return {
        "statusCode": 200
    }

