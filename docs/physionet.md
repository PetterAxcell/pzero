# PhysioNet Loading

The dataset is expected to be released on PhysioNet under controlled access. This repository is ready for that workflow, but the final project slug must be supplied once PhysioNet publishes the landing page.

## Download

Install and configure a PhysioNet-compatible downloader such as `wget`. Then run:

```bash
PHYSIONET_PROJECT="project-slug/1.0.0" ./scripts/download_physionet.sh data/raw
```

The script downloads the release into `data/raw/`. If PhysioNet distributes a ZIP archive, leave it in `data/raw/`; the loader can read from a ZIP path or from extracted CSV files.

## Expected Environment

| Variable | Purpose |
| --- | --- |
| `PHYSIONET_PROJECT` | PhysioNet files path, for example `project-slug/1.0.0`. |
| `PHYSIONET_USERNAME` | Optional username passed to `wget`. |
| `PHYSIONET_PASSWORD` | Optional password passed to `wget`. If omitted, `wget` prompts when needed. |

## Load After Download

PostgreSQL:

```bash
docker compose up -d postgres
docker compose run --rm loader-postgres
```

MariaDB:

```bash
docker compose up -d mariadb
docker compose run --rm loader-mariadb
```

If the final PhysioNet file names differ from the current working CSV bundle, update the aliases in `scripts/pzero_load.py`.

