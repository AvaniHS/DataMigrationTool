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