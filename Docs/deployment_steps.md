# Deployment Steps

# AWS Data Ingestion Framework

Version: 1.0
Author: Mohammed Zubair Siddiqui

---

# 1. Introduction

This document provides step-by-step instructions for deploying the AWS Data Ingestion Framework.

The deployment includes:

* S3 bucket creation
* IAM role configuration
* AWS Glue job creation
* AWS Lambda configuration
* Event-based processing

---

# 2. Prerequisites

Before deployment, ensure the following are available:

* AWS Account
* IAM permissions
* AWS Glue access
* AWS Lambda access
* Amazon S3 access

---

# 3. Create S3 Buckets

Create the following S3 buckets:

```text
input-bucket
output-bucket
```

Recommended configuration:

* Block public access: Enabled
* Versioning: Enabled
* Server-side encryption: Enabled

---

# 4. Create Folder Structure

Input bucket structure:

```text
entity/
    Full_load/
        csv_files/
        json_files/
        xml_files/
        sql_files/

entity/
    Delta_load/
        csv_files/
        json_files/
        xml_files/
        sql_files/
```

Output bucket structure:

```text
bronze/
```

---

# 5. Create IAM Role for AWS Glue

Create an IAM role for Glue.

Attach permissions:

* AWSGlueServiceRole
* AmazonS3FullAccess

Assign the role to all Glue jobs.

---

# 6. Create AWS Glue Jobs

Create individual Glue jobs for:

* CSV processing
* XML processing
* JSON processing
* SQL processing

Recommended settings:

| Setting           | Value    |
| ----------------- | -------- |
| Glue Version      | Latest   |
| Language          | Python   |
| Worker Type       | Standard |
| Number of Workers | 2        |

---

# 7. Upload Glue Scripts

Upload PySpark scripts to the repository or S3.

Examples:

```text
glue/
    csv_to_parquet.py
    xml_to_parquet.py
    json_to_parquet.py
    sql_to_parquet.py
```

---

# 8. Configure XML Support

Upload the Spark XML library.

Configure the Glue job parameter:

```text
--extra-jars
```

This enables XML processing support.

---

# 9. Create Lambda Function

Create a Lambda function.

Runtime:

* Python 3.x

Purpose:

* Detect file uploads.
* Trigger Glue jobs.
* Pass file information.

---

# 10. Configure Lambda Permissions

Grant the Lambda execution role permission to:

* Start Glue jobs
* Write CloudWatch logs

Required permissions:

* glue:StartJobRun
* logs:CreateLogGroup
* logs:PutLogEvents

---

# 11. Configure S3 Event Triggers

Configure S3 events.

Event type:

* Object Created

Target:

* AWS Lambda

This enables automatic processing of uploaded files.

---

# 12. Pass Parameters to Glue Jobs

Lambda passes the uploaded S3 object path to Glue.

Example parameters:

```text
--s3_key
```

Glue processes only the uploaded file.

---

# 13. Upload Sample Files

Upload files into S3.

Examples:

```text
customers/Full_load/csv_files/
orders/Delta_load/json_files/
products/Full_load/xml_files/
```

---

# 14. Execute Glue Jobs

Jobs can execute:

* Automatically through Lambda.
* Manually from the Glue Console.

Monitor execution status.

---

# 15. Validate Output

Verify Parquet files are generated.

Output example:

```text
bronze/
    customers/
    orders/
    products/
```

Validate:

* File generation
* Record counts
* Data quality

---

# 16. Monitor Execution

Monitor:

* Glue job runs
* Lambda logs
* CloudWatch logs

Review failures and execution statistics.

---

# 17. Troubleshooting

| Issue                  | Resolution                |
| ---------------------- | ------------------------- |
| Glue job failure       | Verify IAM permissions    |
| S3 access failure      | Check bucket policies     |
| Lambda failure         | Review CloudWatch logs    |
| XML processing failure | Verify Spark XML library  |
| Missing files          | Validate folder structure |

---

# 18. Cleanup

After testing:

* Remove temporary files.
* Stop unused resources.
* Delete test data.

This helps reduce AWS costs.

---

# 19. Future Improvements

Potential enhancements include:

* Metadata-driven ingestion.
* Dynamic Glue jobs.
* Workflow orchestration.
* CI/CD pipelines.
* Data quality framework.

---

# 20. Conclusion

Following these deployment steps enables successful deployment of the AWS Data Ingestion Framework and provides automated, scalable, and secure ingestion of multiple data formats into Amazon S3.

