-- ============================================================
-- Migration: mig_multi_server_enterprise_2026
-- Client: client_global_retail_corp
-- Version: 1.0.0
-- ============================================================

START TRANSACTION;

SAVEPOINT bp_step_1;

-- Pulling customer profiles directly from the client's live MySQL CRM Server
-- Bootstrap MYSQL source 'cm' (client_crm_mysql.crm_db.customer_master)
SET @cm_host = 'client-crm-ip';
SET @cm_port = 3306;
SET @cm_database = 'crm_db';
SET @cm_username = 'read_user';
SET @cm_password = 'pass';
DROP TEMPORARY TABLE IF EXISTS _bootstrap_cm;
CREATE TEMPORARY TABLE _bootstrap_cm AS
SELECT *
FROM `fed_client_crm_mysql`.`customer_master`;

-- Joining physical metadata from an offline CSV dump hosted on S3
-- Bootstrap CSV source 'gam' (geo_address_mapping.csv)
SET @gam_s3_uri = 's3://client-migration-dump/historical_archives/geo_address_mapping.csv';
SET @gam_aws_region = 'us-west-2';
SET @gam_local_csv = '/tmp/migration/geo_address_mapping.csv';
-- Pre-step: download CSV from S3 to @alias_local_csv before executing this script.
DROP TEMPORARY TABLE IF EXISTS _bootstrap_gam;
CREATE TEMPORARY TABLE _bootstrap_gam AS
SELECT *
FROM `fed_client_archival_s3`.`csv`;
-- Alternate local load path:
-- LOAD DATA LOCAL INFILE @gam_local_csv
-- INTO TABLE _bootstrap_gam
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n' IGNORE 1 ROWS;

WITH
  -- Pulling customer profiles directly from the client's live MySQL CRM Server
  bp1_stg_cm AS (
    SELECT *
    FROM _bootstrap_cm
  ),
  -- Joining physical metadata from an offline CSV dump hosted on S3
  bp1_stg_gam AS (
    SELECT *
    FROM _bootstrap_gam
  ),
  bp1_pre_filtered_cm AS (
    SELECT *
    FROM bp1_stg_cm AS cm
    WHERE cm.status = 'ACTIVE'
  ),
  bp1_joined_cm AS (
    SELECT cm.*, gam.*
    FROM bp1_pre_filtered_cm AS cm
    LEFT JOIN bp1_stg_gam AS gam
      ON gam.legacy_cust_id = cm.id
  ),
  bp1_calculation_layer AS (
    SELECT cm.*, gam.*, REGEXP_REPLACE(cm.phone_raw, '[^0-9+]', '') AS formatted_phone
    FROM bp1_pre_filtered_cm AS cm
    LEFT JOIN bp1_stg_gam AS gam
      ON gam.legacy_cust_id = cm.id
  ),
  bp1_target_projection AS (
    SELECT
        CASE WHEN cm.global_uuid IS NULL OR TRIM(cm.global_uuid) = '' THEN NULL WHEN TRIM(cm.global_uuid) REGEXP '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$' THEN TRIM(cm.global_uuid) ELSE NULL END AS id,
        NULLIF(TRIM(CAST(cm.company_legal_name AS CHAR)), '') AS company_name,
        NULLIF(TRIM(CAST(formatted_phone AS CHAR)), '') AS phone,
        NULLIF(TRIM(CAST(COALESCE(gam.country_code, 'USA') AS CHAR)), '') AS country_iso
    FROM bp1_calculation_layer
  )
INSERT INTO core.customers (id, company_name, phone, country_iso)
SELECT id, company_name, phone, country_iso
FROM bp1_target_projection
ON DUPLICATE KEY UPDATE company_name = VALUES(company_name), phone = VALUES(phone), country_iso = VALUES(country_iso);

RELEASE SAVEPOINT bp_step_1;

COMMIT;

START TRANSACTION;

SAVEPOINT bp_step_2;

-- Pulling invoice headers from the client's centralized SQL Server database
-- Bootstrap MSSQL source 'tih' (client_billing_mssql.dbo.tbl_invoice_hdr)
-- Requires ODBC bridge or linked-server mapping into MySQL federated schema.
SET @tih_host = 'client-billing-ip';
SET @tih_port = 1433;
SET @tih_database = 'finance_db';
SET @tih_username = 'read_user';
SET @tih_password = 'pass';
DROP TEMPORARY TABLE IF EXISTS _bootstrap_tih;
CREATE TEMPORARY TABLE _bootstrap_tih AS
SELECT *
FROM `fed_client_billing_mssql`.`tbl_invoice_hdr`;

-- Invoice lines are inside the exact same SQL Server as the headers
-- Bootstrap MSSQL source 'til' (client_billing_mssql.dbo.tbl_invoice_lines)
-- Requires ODBC bridge or linked-server mapping into MySQL federated schema.
SET @til_host = 'client-billing-ip';
SET @til_port = 1433;
SET @til_database = 'finance_db';
SET @til_username = 'read_user';
SET @til_password = 'pass';
DROP TEMPORARY TABLE IF EXISTS _bootstrap_til;
CREATE TEMPORARY TABLE _bootstrap_til AS
SELECT *
FROM `fed_client_billing_mssql`.`tbl_invoice_lines`;

-- JOIN SCENARIO WITH COMPLEX CASE KEYS: Pulling store details from a separate POS live server
-- Bootstrap POSTGRESQL source 'st' (client_pos_logs.public.store_terminals)
-- Requires PostgreSQL federated bridge mapped into MySQL.
SET @st_host = 'client-pos-ip';
SET @st_port = 5432;
SET @st_database = 'retail_logs';
SET @st_username = 'pos_viewer';
SET @st_password = 'pass';
DROP TEMPORARY TABLE IF EXISTS _bootstrap_st;
CREATE TEMPORARY TABLE _bootstrap_st AS
SELECT *
FROM `fed_client_pos_logs`.`store_terminals`;

SET @bp2_chunk_min = 0;
SET @bp2_chunk_size = 25000;
SET @bp2_chunk_max = (SELECT COALESCE(MAX(tih.id), 0) FROM _bootstrap_tih AS tih);

WHILE @bp2_chunk_min <= @bp2_chunk_max DO
SAVEPOINT bp_step_2_chunk;
WITH
  -- Pulling invoice headers from the client's centralized SQL Server database
  bp2_stg_tih AS (
    SELECT *
    FROM _bootstrap_tih
  ),
  -- Invoice lines are inside the exact same SQL Server as the headers
  bp2_stg_til AS (
    SELECT *
    FROM _bootstrap_til
  ),
  -- JOIN SCENARIO WITH COMPLEX CASE KEYS: Pulling store details from a separate POS live server
  bp2_stg_st AS (
    SELECT *
    FROM _bootstrap_st
  ),
  bp2_chunk_filtered AS (
    SELECT *
    FROM bp2_stg_tih AS tih
    WHERE tih.id > @bp2_chunk_min AND tih.id <= @bp2_chunk_min + @bp2_chunk_size
  ),
  bp2_pre_filtered_tih AS (
    SELECT *
    FROM bp2_chunk_filtered AS tih
    WHERE tih.invoice_date >= '2022-01-01'
  ),
  bp2_joined_tih AS (
    SELECT tih.*, til.*, st.*
    FROM bp2_pre_filtered_tih AS tih
    INNER JOIN bp2_stg_til AS til
      ON til.hdr_id = tih.id
    LEFT JOIN bp2_stg_st AS st
      ON CASE WHEN tih.channel_type = 'RETAIL' THEN tih.terminal_identifier ELSE tih.fallback_hq_identifier END = st.terminal_uid
  ),
  bp2_calculation_layer AS (
    SELECT tih.*, til.*, st.*, CONCAT(COALESCE(st.store_prefix, 'WEB'), '-', tih.invoice_number) AS system_invoice_key, (til.unit_price * til.quantity_billed) AS calculated_line_cost
    FROM bp2_pre_filtered_tih AS tih
    INNER JOIN bp2_stg_til AS til
      ON til.hdr_id = tih.id
    LEFT JOIN bp2_stg_st AS st
      ON CASE WHEN tih.channel_type = 'RETAIL' THEN tih.terminal_identifier ELSE tih.fallback_hq_identifier END = st.terminal_uid
  ),
  bp2_target_projection AS (
    SELECT
        NULLIF(TRIM(CAST('RETAIL_ENTERPRISE_GLOBAL' AS CHAR)), '') AS tenant_id,
        NULLIF(TRIM(CAST(system_invoice_key AS CHAR)), '') AS invoice_no,
        CASE WHEN til.line_id IS NULL OR TRIM(til.line_id) = '' THEN NULL WHEN TRIM(CAST(til.line_id AS CHAR)) REGEXP '^-?[0-9]+$' THEN CAST(til.line_id AS BIGINT) ELSE NULL END AS line_item_id,
        CASE WHEN calculated_line_cost IS NULL OR TRIM(calculated_line_cost) = '' THEN NULL WHEN TRIM(CAST(calculated_line_cost AS CHAR)) REGEXP '^-?[0-9]+(\.[0-9]+)?$' THEN CAST(calculated_line_cost AS DECIMAL(12,4)) ELSE NULL END AS subtotal_amount,
        CASE WHEN CASE WHEN tih.tax_exempt_flag = 1 THEN 0.0000 ELSE (derivations.calculated_line_cost * 0.18) END IS NULL OR TRIM(CASE WHEN tih.tax_exempt_flag = 1 THEN 0.0000 ELSE (derivations.calculated_line_cost * 0.18) END) = '' THEN NULL WHEN TRIM(CAST(CASE WHEN tih.tax_exempt_flag = 1 THEN 0.0000 ELSE (derivations.calculated_line_cost * 0.18) END AS CHAR)) REGEXP '^-?[0-9]+(\.[0-9]+)?$' THEN CAST(CASE WHEN tih.tax_exempt_flag = 1 THEN 0.0000 ELSE (derivations.calculated_line_cost * 0.18) END AS DECIMAL(12,4)) ELSE NULL END AS tax_amount,
        CASE WHEN tih.invoice_date IS NULL OR TRIM(tih.invoice_date) = '' THEN NULL ELSE STR_TO_DATE(tih.invoice_date, '%Y-%m-%d') END AS invoice_date
    FROM bp2_calculation_layer
  )
INSERT INTO billing.billing_details (tenant_id, invoice_no, line_item_id, subtotal_amount, tax_amount, invoice_date)
SELECT tenant_id, invoice_no, line_item_id, subtotal_amount, tax_amount, invoice_date
FROM bp2_target_projection
ON DUPLICATE KEY UPDATE subtotal_amount = VALUES(subtotal_amount), tax_amount = VALUES(tax_amount), invoice_date = VALUES(invoice_date)
;
SET @bp2_chunk_min = @bp2_chunk_min + @bp2_chunk_size;
RELEASE SAVEPOINT bp_step_2_chunk;
END WHILE;

RELEASE SAVEPOINT bp_step_2;

COMMIT;

START TRANSACTION;

SAVEPOINT bp_step_3;

-- Bootstrap CSV source 'hih' (historical_invoice_headers_2021.csv)
SET @hih_s3_uri = 's3://client-migration-dump/historical_archives/historical_invoice_headers_2021.csv';
SET @hih_aws_region = 'us-west-2';
SET @hih_local_csv = '/tmp/migration/historical_invoice_headers_2021.csv';
-- Pre-step: download CSV from S3 to @alias_local_csv before executing this script.
DROP TEMPORARY TABLE IF EXISTS _bootstrap_hih;
CREATE TEMPORARY TABLE _bootstrap_hih AS
SELECT *
FROM `fed_client_archival_s3`.`csv`;
-- Alternate local load path:
-- LOAD DATA LOCAL INFILE @hih_local_csv
-- INTO TABLE _bootstrap_hih
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- Bootstrap CSV source 'hil' (historical_invoice_lines_2021.csv)
SET @hil_s3_uri = 's3://client-migration-dump/historical_archives/historical_invoice_lines_2021.csv';
SET @hil_aws_region = 'us-west-2';
SET @hil_local_csv = '/tmp/migration/historical_invoice_lines_2021.csv';
-- Pre-step: download CSV from S3 to @alias_local_csv before executing this script.
DROP TEMPORARY TABLE IF EXISTS _bootstrap_hil;
CREATE TEMPORARY TABLE _bootstrap_hil AS
SELECT *
FROM `fed_client_archival_s3`.`csv`;
-- Alternate local load path:
-- LOAD DATA LOCAL INFILE @hil_local_csv
-- INTO TABLE _bootstrap_hil
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n' IGNORE 1 ROWS;

WITH
  bp3_stg_hih AS (
    SELECT *
    FROM _bootstrap_hih
  ),
  bp3_stg_hil AS (
    SELECT *
    FROM _bootstrap_hil
  ),
  bp3_pre_filtered_hih AS (
    SELECT *
    FROM bp3_stg_hih AS hih
  ),
  bp3_joined_hih AS (
    SELECT hih.*, hil.*
    FROM bp3_pre_filtered_hih AS hih
    INNER JOIN bp3_stg_hil AS hil
      ON hil.parent_invoice_id = hih.raw_id
  ),
  bp3_calculation_layer AS (
    SELECT hih.*, hil.*, CONCAT('ARCHIVE-', hih.raw_id) AS historical_key
    FROM bp3_pre_filtered_hih AS hih
    INNER JOIN bp3_stg_hil AS hil
      ON hil.parent_invoice_id = hih.raw_id
  ),
  bp3_target_projection AS (
    SELECT
        NULLIF(TRIM(CAST('RETAIL_ENTERPRISE_GLOBAL' AS CHAR)), '') AS tenant_id,
        NULLIF(TRIM(CAST(historical_key AS CHAR)), '') AS invoice_no,
        CASE WHEN hil.row_index IS NULL OR TRIM(hil.row_index) = '' THEN NULL WHEN TRIM(CAST(hil.row_index AS CHAR)) REGEXP '^-?[0-9]+$' THEN CAST(hil.row_index AS BIGINT) ELSE NULL END AS line_item_id,
        CASE WHEN hil.net_cost IS NULL OR TRIM(hil.net_cost) = '' THEN NULL WHEN TRIM(CAST(hil.net_cost AS CHAR)) REGEXP '^-?[0-9]+(\.[0-9]+)?$' THEN CAST(hil.net_cost AS DECIMAL(12,4)) ELSE NULL END AS subtotal_amount,
        CASE WHEN hil.tax_cost IS NULL OR TRIM(hil.tax_cost) = '' THEN NULL WHEN TRIM(CAST(hil.tax_cost AS CHAR)) REGEXP '^-?[0-9]+(\.[0-9]+)?$' THEN CAST(hil.tax_cost AS DECIMAL(12,4)) ELSE NULL END AS tax_amount,
        CASE WHEN hih.post_date IS NULL OR TRIM(hih.post_date) = '' THEN NULL ELSE STR_TO_DATE(hih.post_date, '%Y-%m-%d') END AS invoice_date
    FROM bp3_calculation_layer
  )
INSERT INTO billing.billing_details (tenant_id, invoice_no, line_item_id, subtotal_amount, tax_amount, invoice_date)
SELECT tenant_id, invoice_no, line_item_id, subtotal_amount, tax_amount, invoice_date
FROM bp3_target_projection
ON DUPLICATE KEY UPDATE subtotal_amount = VALUES(subtotal_amount), tax_amount = VALUES(tax_amount), invoice_date = VALUES(invoice_date);

RELEASE SAVEPOINT bp_step_3;

COMMIT;