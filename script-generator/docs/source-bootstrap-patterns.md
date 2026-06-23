# Source Bootstrap Patterns (MySQL Target)

This document describes how generated migration scripts bootstrap remote sources into
`_bootstrap_{alias}` temporary tables before the CTE pipeline runs.

## Overview

| Source `connections[type]` | Bootstrap approach | MySQL prerequisite |
|----------------------------|--------------------|--------------------|
| `MYSQL` | `CREATE TEMPORARY TABLE _bootstrap_{alias} AS SELECT * FROM fed_{connection_ref}.{table}` | FEDERATED or replication bridge schema `fed_{connection_ref}` |
| `MSSQL` | Same pattern via ODBC/linked-server bridge | ODBC driver + mapped federated schema `fed_{connection_ref}` |
| `POSTGRESQL` | Same pattern via PostgreSQL federated bridge | Bridge tables in `fed_{connection_ref}` |
| `CSV_S3_BUCKET` | `CREATE TEMPORARY TABLE` from `fed_{connection_ref}.{csv_file}` + optional `LOAD DATA LOCAL INFILE` | CSV staged to local path or preloaded staging table |

## Connection variables

Each database source emits session variables for operator override:

```sql
SET @cm_host = 'client-crm-ip';
SET @cm_port = 3306;
SET @cm_database = 'crm_db';
SET @cm_username = 'read_user';
SET @cm_password = 'pass';
```

CSV sources emit:

```sql
SET @gam_s3_uri = 's3://bucket/path/file.csv';
SET @gam_aws_region = 'us-west-2';
SET @gam_local_csv = '/tmp/migration/file.csv';
```

## Federated schema naming

- Schema: `fed_{connection_ref}` (example: `fed_client_crm_mysql`)
- Table: source `table_name` or sanitized CSV file name

Operators must provision federated/bridge objects to match generated references before
running the script.

## S3 CSV workflow

1. Download CSV from `@alias_s3_uri` to `@alias_local_csv` (external step or `aws s3 cp`).
2. Either load into `fed_{connection_ref}` staging table, or uncomment the generated
   `LOAD DATA LOCAL INFILE` block in the preamble.
3. Bootstrap temp table is populated for CTE `stg_{alias}` stages.

## Security note

Generated scripts currently embed credentials in `SET` statements for self-contained
execution. For production, prefer parameterized secrets injection or pre-provisioned
bridge users with read-only grants.
