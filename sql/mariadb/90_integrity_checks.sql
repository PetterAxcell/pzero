SELECT 'demographics_without_ward_stay' AS check_name, COUNT(*) AS issue_count
FROM demographics d
LEFT JOIN ward_stays w ON w.patient_ref = d.patient_ref
WHERE w.patient_ref IS NULL
UNION ALL
SELECT 'ward_stays_without_demographics', COUNT(*)
FROM ward_stays w
LEFT JOIN demographics d ON d.patient_ref = w.patient_ref
WHERE d.patient_ref IS NULL
UNION ALL
SELECT 'diagnostics_without_ward_stay_episode', COUNT(*)
FROM diagnostics dx
LEFT JOIN ward_stays w ON w.episode_ref = dx.episode_ref
WHERE w.episode_ref IS NULL
UNION ALL
SELECT 'labs_without_ward_stay', COUNT(*)
FROM labs l
LEFT JOIN ward_stays w ON w.stay_id = l.stay_id
WHERE w.stay_id IS NULL
UNION ALL
SELECT 'vitals_without_ward_stay', COUNT(*)
FROM vitals v
LEFT JOIN ward_stays w ON w.stay_id = v.stay_id
WHERE w.stay_id IS NULL
UNION ALL
SELECT 'labs_without_laboratory_dictionary', COUNT(*)
FROM labs l
LEFT JOIN laboratory_dictionary ld ON ld.lab_sap_ref = l.lab_sap_ref
WHERE ld.lab_sap_ref IS NULL
UNION ALL
SELECT 'duplicate_laboratory_dictionary_codes', COUNT(*)
FROM (
    SELECT lab_sap_ref
    FROM laboratory_dictionary
    GROUP BY lab_sap_ref
    HAVING COUNT(*) > 1
) duplicate_lab_codes
UNION ALL
SELECT 'duplicate_vitals_value_dictionary_keys', COUNT(*)
FROM (
    SELECT rc_sap_ref, result_txt
    FROM vitals_values_dictionary
    GROUP BY rc_sap_ref, result_txt
    HAVING COUNT(*) > 1
) duplicate_vital_keys;

