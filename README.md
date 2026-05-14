# pzero

Reproducible database build for the Project Zero ward deterioration dataset.

This repository is designed for data analysts, data managers, and secondary data users who want to load the released CSV files into either PostgreSQL or MariaDB. It supports local CSV files, a local ZIP archive, and a future PhysioNet download workflow once the public project slug is available.

## Dataset

Project Zero is a longitudinal, anonymized electronic health record dataset of adult general ward stays from Hospital Clinic de Barcelona. The core table is `ward_stays`, linked to patient-level demographics, ICD-10 diagnostics, vital sign observations, laboratory results, and two reference dictionaries.

Expected source files:

| File | Loaded table | Notes |
| --- | --- | --- |
| `ward_stays.csv` | `ward_stays` | Central ward-stay table and outcome fields. |
| `demographic.csv` or `demographics.csv` | `demographics` | Patient-level static data. The current working ZIP uses the singular file name. |
| `diagnostics.csv` | `diagnostics` | ICD-10 diagnoses linked by `episode_ref`. |
| `vitals.csv` | `vitals` | Long-format vital sign observations. |
| `labs.csv` | `labs` | Long-format laboratory results. |
| `laboratory_dic.csv` | `laboratory_dictionary` | Laboratory code dictionary. |
| `vitals_values_dic.csv` | `vitals_values_dictionary` | Categorical vital-sign value dictionary. |

The CSV data are not stored in this repository. Put them under `data/raw/`, either extracted or as a ZIP file.

## Quick Start: PostgreSQL

```bash
cp .env.example .env
mkdir -p data/raw
# Put csvs_P0.zip or the extracted CSV files in data/raw/

docker compose up -d postgres
docker compose run --rm loader-postgres
docker compose exec postgres psql -U pzero -d pzero
```

Equivalent Make targets:

```bash
make up-postgres
make load-postgres
make psql
```

## Quick Start: MariaDB

```bash
cp .env.example .env
mkdir -p data/raw
# Put csvs_P0.zip or the extracted CSV files in data/raw/

docker compose up -d mariadb
docker compose run --rm loader-mariadb
docker compose exec mariadb mariadb -u pzero -ppzero pzero
```

Equivalent Make targets:

```bash
make up-mariadb
make load-mariadb
make mariadb
```

## Loading Without Docker

Install the Python loader dependencies:

```bash
python -m pip install -r requirements.txt
```

Load PostgreSQL:

```bash
python scripts/pzero_load.py \
  --engine postgres \
  --source data/raw \
  --host localhost \
  --port 5432 \
  --database pzero \
  --user pzero \
  --password pzero
```

Load MariaDB:

```bash
python scripts/pzero_load.py \
  --engine mariadb \
  --source data/raw \
  --host localhost \
  --port 3306 \
  --database pzero \
  --user pzero \
  --password pzero
```

`--source` may point to a directory containing CSV files or to a ZIP archive.

## PhysioNet

The manuscript references a controlled-access PhysioNet release. Once the final PhysioNet project slug is known, set `PHYSIONET_PROJECT` and run:

```bash
PHYSIONET_PROJECT="project-slug/1.0.0" ./scripts/download_physionet.sh data/raw
```

See [docs/physionet.md](docs/physionet.md) for details.

## Schema Notes

The SQL schemas define practical database types and indexes for exploratory analysis and model development. They intentionally avoid strict foreign-key constraints on the high-volume observation tables because the current working CSV bundle contains a small number of `stay_id` values in `labs` and `vitals` that are not present in `ward_stays`. Use the integrity-check scripts to quantify this for each release:

```bash
docker compose exec -T postgres psql -U pzero -d pzero < sql/postgres/90_integrity_checks.sql
```

or:

```bash
docker compose exec -T mariadb mariadb -u pzero -ppzero pzero < sql/mariadb/90_integrity_checks.sql
```

More detail is available in [docs/data_model.md](docs/data_model.md).

## Repository Layout

```text
data/raw/              Source CSV files or ZIP archive, ignored by git
docs/                  Dataset and loading notes
scripts/               Loader and PhysioNet helper scripts
sql/postgres/          PostgreSQL DDL, indexes, and integrity checks
sql/mariadb/           MariaDB DDL, indexes, and integrity checks
docker-compose.yml     PostgreSQL, MariaDB, and loader services
```

## Primary Outcome

The `ward_stay_outcomes` view exposes a derived `deterioration_outcome` field:

```sql
CASE
  WHEN to_icu = 1 OR hosp_mortality_bin = 1 THEN 1
  ELSE 0
END
```

For predictive modelling, define an explicit index time and only use observations timestamped before that index time to avoid target leakage.
