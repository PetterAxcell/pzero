# Data Model

This repository loads the Project Zero CSV release into a relational database while preserving the long-format structure of the source files.

## Tables

| Table | Grain | Main join key |
| --- | --- | --- |
| `ward_stays` | One row per anonymized ward stay | `stay_id` |
| `demographics` | One row per anonymized patient | `patient_ref` |
| `diagnostics` | One row per ICD-10 diagnosis within an episode | `episode_ref`, `diag_id` |
| `vitals` | One row per vital sign observation | `stay_id`, `rc_sap_ref`, `result_date` |
| `labs` | One row per laboratory result | `stay_id`, `lab_sap_ref`, `extract_date` |
| `laboratory_dictionary` | Laboratory concept metadata | `lab_sap_ref` |
| `vitals_values_dictionary` | Categorical vital-sign value metadata | `rc_sap_ref`, `result_txt` |

## Logical Relationships

`ward_stays` is the central table:

```text
demographics.patient_ref      -> ward_stays.patient_ref
diagnostics.episode_ref       -> ward_stays.episode_ref
vitals.stay_id                -> ward_stays.stay_id
labs.stay_id                  -> ward_stays.stay_id
labs.lab_sap_ref              -> laboratory_dictionary.lab_sap_ref
vitals.result_txt             -> vitals_values_dictionary.result_txt
```

These relationships are documented and indexed, but they are not enforced as database foreign keys by default. The working CSV bundle profiled during repository creation contained a small number of observation rows whose `stay_id` was absent from `ward_stays`, and both dictionary files contained duplicate lookup keys. Avoiding hard constraints keeps the raw release loadable and auditable.

Run the integrity checks after loading:

```bash
psql -h localhost -U pzero -d pzero -f sql/postgres/90_integrity_checks.sql
```

or:

```bash
mariadb -h localhost -u pzero -ppzero pzero < sql/mariadb/90_integrity_checks.sql
```

## Profile of the Working CSV Bundle

The attached working ZIP profiled on 2026-05-14 had these row counts. The final PhysioNet release may differ.

| CSV file | Rows |
| --- | ---: |
| `ward_stays.csv` | 23,833 |
| `demographic.csv` | 18,632 |
| `diagnostics.csv` | 230,248 |
| `vitals.csv` | 9,646,044 |
| `labs.csv` | 5,403,329 |
| `laboratory_dic.csv` | 5,115 |
| `vitals_values_dic.csv` | 36 |

## Outcome View

The `ward_stay_outcomes` view exposes the derived binary outcome:

```sql
CASE
  WHEN to_icu = 1 OR hosp_mortality_bin = 1 THEN 1
  ELSE 0
END AS deterioration_outcome
```

For prediction studies, this outcome must be paired with an explicit index time. Only observations timestamped before the index time should be used as predictors.

## Timestamp Handling

All timestamps are loaded as timestamp/datetime values without timezone conversion. The dataset timestamps have already been shifted during anonymization, and the database build preserves the released values.

