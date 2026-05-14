CREATE INDEX IF NOT EXISTS idx_ward_stays_episode_ref ON ward_stays (episode_ref);
CREATE INDEX IF NOT EXISTS idx_ward_stays_patient_ref ON ward_stays (patient_ref);
CREATE INDEX IF NOT EXISTS idx_ward_stays_dates ON ward_stays (start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_ward_stays_outcome ON ward_stays (to_icu, hosp_mortality_bin);

CREATE INDEX IF NOT EXISTS idx_diagnostics_episode_ref ON diagnostics (episode_ref);
CREATE INDEX IF NOT EXISTS idx_diagnostics_icd10_code ON diagnostics (icd10_code);
CREATE INDEX IF NOT EXISTS idx_diagnostics_poa ON diagnostics (poa);

CREATE INDEX IF NOT EXISTS idx_laboratory_dictionary_code ON laboratory_dictionary (lab_sap_ref);
CREATE INDEX IF NOT EXISTS idx_vitals_values_dictionary_code ON vitals_values_dictionary (rc_sap_ref, result_txt);

CREATE INDEX IF NOT EXISTS idx_labs_stay_time ON labs (stay_id, extract_date);
CREATE INDEX IF NOT EXISTS idx_labs_code_time ON labs (lab_sap_ref, extract_date);

CREATE INDEX IF NOT EXISTS idx_vitals_stay_time ON vitals (stay_id, result_date);
CREATE INDEX IF NOT EXISTS idx_vitals_code_time ON vitals (rc_sap_ref, result_date);

ANALYZE TABLE demographics, ward_stays, diagnostics, laboratory_dictionary, vitals_values_dictionary, labs, vitals;

