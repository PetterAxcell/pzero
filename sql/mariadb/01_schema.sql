CREATE TABLE IF NOT EXISTS demographics (
    patient_ref BIGINT NOT NULL PRIMARY KEY,
    sex SMALLINT NOT NULL,
    demog_id BIGINT NOT NULL UNIQUE,
    natio_ref VARCHAR(16) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ward_stays (
    stay_id BIGINT NOT NULL PRIMARY KEY,
    episode_ref BIGINT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    care_level_type_ref VARCHAR(16) NOT NULL,
    ou_med_ref VARCHAR(16) NOT NULL,
    seq_num INT NOT NULL,
    next_care_level VARCHAR(16),
    to_icu TINYINT NOT NULL,
    icu_los DOUBLE,
    hosp_adm_date DATETIME NOT NULL,
    hosp_disch_date DATETIME NOT NULL,
    hosp_los INT NOT NULL,
    hosp_mortality_bin TINYINT NOT NULL,
    hosp_mortality_date DATE,
    discharge_to_dead_interval DOUBLE,
    patient_ref BIGINT NOT NULL,
    age_at_admission DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS diagnostics (
    episode_ref BIGINT NOT NULL,
    diagnosis_class VARCHAR(8) NOT NULL,
    poa VARCHAR(8) NOT NULL,
    diag_id BIGINT NOT NULL,
    icd10_code VARCHAR(16),
    PRIMARY KEY (episode_ref, diag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS laboratory_dictionary (
    dictionary_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    lab_sap_ref VARCHAR(16) NOT NULL,
    lab_descr VARCHAR(128),
    units VARCHAR(64),
    loinc_code VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vitals_values_dictionary (
    dictionary_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    rc_sap_ref VARCHAR(32) NOT NULL,
    result_txt VARCHAR(32) NOT NULL,
    descr VARCHAR(64) NOT NULL,
    english_descr VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS labs (
    lab_event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    stay_id BIGINT NOT NULL,
    lab_sap_ref VARCHAR(16) NOT NULL,
    result_num DOUBLE,
    result_txt VARCHAR(128),
    extract_date DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS vitals (
    vital_event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    stay_id BIGINT NOT NULL,
    result_date DATETIME NOT NULL,
    result_num DOUBLE,
    result_txt VARCHAR(32),
    rc_sap_ref VARCHAR(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE OR REPLACE VIEW ward_stay_outcomes AS
SELECT
    stay_id,
    episode_ref,
    patient_ref,
    start_date,
    end_date,
    to_icu,
    hosp_mortality_bin,
    CASE
        WHEN to_icu = 1 OR hosp_mortality_bin = 1 THEN 1
        ELSE 0
    END AS deterioration_outcome
FROM ward_stays;

