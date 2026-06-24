import boto3

def lambda_handler(event, context):
    glue = boto3.client('glue')

    print("Event:", event)

    # Log all uploaded files
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']
        print(f"📂 New CSV uploaded: s3://{bucket}/{s3_key}")

    # Start Glue job
    response = glue.start_job_run(
        JobName='csv-to-parquet'   # 🔹 replace with your Glue job name
    )

    print("🚀 Glue job triggered:", response['JobRunId'])
    return {
        'statusCode': 200,
        'body': 'Glue job started successfully'
    }

