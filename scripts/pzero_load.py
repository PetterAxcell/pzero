#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import csv
import os
import shutil
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TABLE_ORDER = (
    "demographics",
    "ward_stays",
    "diagnostics",
    "laboratory_dictionary",
    "vitals_values_dictionary",
    "labs",
    "vitals",
)


@dataclass(frozen=True)
class CsvTable:
    name: str
    filenames: tuple[str, ...]
    source_columns: tuple[str, ...]
    target_columns: tuple[str, ...]


TABLES = (
    CsvTable(
        name="demographics",
        filenames=("demographic.csv", "demographics.csv"),
        source_columns=("patient_ref", "sex", "demog_id", "natio_ref"),
        target_columns=("patient_ref", "sex", "demog_id", "natio_ref"),
    ),
    CsvTable(
        name="ward_stays",
        filenames=("ward_stays.csv",),
        source_columns=(
            "stay_id",
            "episode_ref",
            "start_date",
            "end_date",
            "care_level_type_ref",
            "ou_med_ref",
            "seq_num",
            "next_care_level",
            "to_icu",
            "icu_los",
            "hosp_adm_date",
            "hosp_disch_date",
            "hosp_los",
            "hosp_mortality_bin",
            "hosp_mortality_date",
            "discharge_to_dead_interval",
            "patient_ref",
            "age_at_admission",
        ),
        target_columns=(
            "stay_id",
            "episode_ref",
            "start_date",
            "end_date",
            "care_level_type_ref",
            "ou_med_ref",
            "seq_num",
            "next_care_level",
            "to_icu",
            "icu_los",
            "hosp_adm_date",
            "hosp_disch_date",
            "hosp_los",
            "hosp_mortality_bin",
            "hosp_mortality_date",
            "discharge_to_dead_interval",
            "patient_ref",
            "age_at_admission",
        ),
    ),
    CsvTable(
        name="diagnostics",
        filenames=("diagnostics.csv",),
        source_columns=("episode_ref", "class", "poa", "diag_id", "icd10_code"),
        target_columns=("episode_ref", "diagnosis_class", "poa", "diag_id", "icd10_code"),
    ),
    CsvTable(
        name="laboratory_dictionary",
        filenames=("laboratory_dic.csv",),
        source_columns=("lab_sap_ref", "lab_descr", "units", "loinc_code"),
        target_columns=("lab_sap_ref", "lab_descr", "units", "loinc_code"),
    ),
    CsvTable(
        name="vitals_values_dictionary",
        filenames=("vitals_values_dic.csv",),
        source_columns=("rc_sap_ref", "result_txt", "descr", "English"),
        target_columns=("rc_sap_ref", "result_txt", "descr", "english_descr"),
    ),
    CsvTable(
        name="labs",
        filenames=("labs.csv",),
        source_columns=("stay_id", "lab_sap_ref", "result_num", "result_txt", "extract_date"),
        target_columns=("stay_id", "lab_sap_ref", "result_num", "result_txt", "extract_date"),
    ),
    CsvTable(
        name="vitals",
        filenames=("vitals.csv",),
        source_columns=("stay_id", "result_date", "result_num", "result_txt", "rc_sap_ref"),
        target_columns=("stay_id", "result_date", "result_num", "result_txt", "rc_sap_ref"),
    ),
)


def log(message: str) -> None:
    print(message, flush=True)


def bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load Project Zero CSV files into PostgreSQL or MariaDB.")
    parser.add_argument("--engine", choices=("postgres", "mariadb"), default=os.getenv("PZERO_ENGINE", "postgres"))
    parser.add_argument("--source", default=os.getenv("PZERO_SOURCE", "data/raw"), help="Directory or ZIP containing CSV files.")
    parser.add_argument("--host", default=os.getenv("PZERO_DB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PZERO_DB_PORT", "5432")))
    parser.add_argument("--database", default=os.getenv("PZERO_DB_NAME", "pzero"))
    parser.add_argument("--user", default=os.getenv("PZERO_DB_USER", "pzero"))
    parser.add_argument("--password", default=os.getenv("PZERO_DB_PASSWORD", "pzero"))
    parser.add_argument("--no-truncate", action="store_true", default=not bool_from_env("PZERO_TRUNCATE", True))
    parser.add_argument("--skip-indexes", action="store_true", default=bool_from_env("PZERO_SKIP_INDEXES", False))
    parser.add_argument("--connect-retries", type=int, default=int(os.getenv("PZERO_CONNECT_RETRIES", "30")))
    args = parser.parse_args()
    if os.getenv("PZERO_DB_PORT") is None and args.engine == "mariadb" and args.port == 5432:
        args.port = 3306
    return args


class DirectoryCsvSource:
    def __init__(self, root: Path):
        self.root = root

    def resolve(self, table: CsvTable) -> Path:
        for filename in table.filenames:
            exact = self.root / filename
            if exact.exists():
                return exact
            matches = sorted(self.root.rglob(filename))
            if matches:
                return matches[0]
        aliases = ", ".join(table.filenames)
        raise FileNotFoundError(f"Missing source file for {table.name}. Expected one of: {aliases}")


def materialize_zip(source_path: Path) -> contextlib.AbstractContextManager[DirectoryCsvSource]:
    @contextlib.contextmanager
    def _materialized_zip() -> Iterable[DirectoryCsvSource]:
        with tempfile.TemporaryDirectory(prefix="pzero_csv_") as temp_dir:
            temp_root = Path(temp_dir)
            with zipfile.ZipFile(source_path) as archive:
                members_by_name = {Path(member.filename).name: member for member in archive.infolist() if not member.is_dir()}
                for table in TABLES:
                    member = next((members_by_name.get(filename) for filename in table.filenames if filename in members_by_name), None)
                    if member is None:
                        aliases = ", ".join(table.filenames)
                        raise FileNotFoundError(f"Missing source file for {table.name} in ZIP. Expected one of: {aliases}")
                    target_name = Path(member.filename).name
                    target_path = temp_root / target_name
                    with archive.open(member) as src, target_path.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
            yield DirectoryCsvSource(temp_root)

    return _materialized_zip()


@contextlib.contextmanager
def materialized_source(source: str) -> Iterable[DirectoryCsvSource]:
    source_path = Path(source)
    if source_path.is_dir():
        directory_source = DirectoryCsvSource(source_path)
        try:
            for table in TABLES:
                directory_source.resolve(table)
            yield directory_source
            return
        except FileNotFoundError as directory_error:
            zip_paths = sorted(path for path in source_path.iterdir() if path.is_file() and zipfile.is_zipfile(path))
            if len(zip_paths) == 1:
                log(f"Using ZIP archive found in source directory: {zip_paths[0].name}")
                with materialize_zip(zip_paths[0]) as zip_source:
                    yield zip_source
                return
            if len(zip_paths) > 1:
                zip_names = ", ".join(path.name for path in zip_paths)
                raise FileNotFoundError(
                    f"Source directory contains multiple ZIP archives ({zip_names}). "
                    "Pass the desired ZIP path with --source."
                ) from directory_error
            raise directory_error
        return

    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    if not zipfile.is_zipfile(source_path):
        raise ValueError(f"Source must be a directory or ZIP archive: {source_path}")

    with materialize_zip(source_path) as zip_source:
        yield zip_source


def validate_csv_header(table: CsvTable, path: Path) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        try:
            actual_columns = next(csv.reader(file))
        except StopIteration as exc:
            raise ValueError(f"{path.name} is empty; expected CSV header for table {table.name}.") from exc

    expected_columns = list(table.source_columns)
    if actual_columns != expected_columns:
        raise ValueError(
            f"{path.name} header does not match table {table.name}. "
            f"Expected exact order: {expected_columns}. Actual: {actual_columns}."
        )


def validate_sources(source: DirectoryCsvSource) -> dict[str, Path]:
    log("Validating source CSV headers...")
    paths: dict[str, Path] = {}
    for table in TABLES:
        path = source.resolve(table)
        validate_csv_header(table, path)
        paths[table.name] = path
    return paths


def table_by_name(name: str) -> CsvTable:
    for table in TABLES:
        if table.name == name:
            return table
    raise KeyError(name)


def sql_file(engine: str, filename: str) -> Path:
    return ROOT / "sql" / engine / filename


def connect_with_retries(connect_fn, retries: int):
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return connect_fn()
        except Exception as exc:  # pragma: no cover - database startup timing
            last_error = exc
            log(f"Database connection failed on attempt {attempt}/{retries}: {exc}")
            time.sleep(min(2 * attempt, 10))
    assert last_error is not None
    raise last_error


def load_postgres(args: argparse.Namespace, paths: dict[str, Path]) -> None:
    try:
        import psycopg
        from psycopg import sql
    except ImportError as exc:  # pragma: no cover - dependency message
        raise RuntimeError("Install PostgreSQL dependencies with: pip install -r requirements.txt") from exc

    def connect():
        return psycopg.connect(
            host=args.host,
            port=args.port,
            dbname=args.database,
            user=args.user,
            password=args.password,
        )

    conn = connect_with_retries(connect, args.connect_retries)
    try:
        with conn.cursor() as cur:
            log("Creating PostgreSQL schema...")
            cur.execute(sql_file("postgres", "01_schema.sql").read_text())
        conn.commit()

        if not args.no_truncate:
            with conn.cursor() as cur:
                log("Truncating existing PostgreSQL tables...")
                cur.execute(
                    "TRUNCATE TABLE vitals, labs, diagnostics, ward_stays, demographics, "
                    "laboratory_dictionary, vitals_values_dictionary RESTART IDENTITY;"
                )
            conn.commit()

        for table in TABLES:
            path = paths[table.name]
            columns = sql.SQL(", ").join(sql.Identifier(column) for column in table.target_columns)
            copy_sql = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')").format(
                sql.Identifier(table.name),
                columns,
            )
            log(f"Loading {path.name} into PostgreSQL table {table.name}...")
            with conn.cursor() as cur, cur.copy(copy_sql) as copy, path.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    copy.write(chunk)
            conn.commit()

        if not args.skip_indexes:
            with conn.cursor() as cur:
                log("Creating PostgreSQL indexes and statistics...")
                cur.execute(sql_file("postgres", "02_indexes.sql").read_text())
            conn.commit()
    finally:
        conn.close()


def split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).rstrip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    tail = "\n".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def execute_mariadb_sql_file(cursor, path: Path) -> None:
    for statement in split_sql_statements(path.read_text()):
        cursor.execute(statement)


def load_mariadb(args: argparse.Namespace, paths: dict[str, Path]) -> None:
    try:
        import pymysql
    except ImportError as exc:  # pragma: no cover - dependency message
        raise RuntimeError("Install MariaDB dependencies with: pip install -r requirements.txt") from exc

    def connect():
        return pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            charset="utf8mb4",
            local_infile=True,
            autocommit=False,
        )

    conn = connect_with_retries(connect, args.connect_retries)
    try:
        with conn.cursor() as cur:
            log("Creating MariaDB schema...")
            execute_mariadb_sql_file(cur, sql_file("mariadb", "01_schema.sql"))
        conn.commit()

        if not args.no_truncate:
            with conn.cursor() as cur:
                log("Truncating existing MariaDB tables...")
                cur.execute("SET FOREIGN_KEY_CHECKS = 0")
                for table_name in reversed(TABLE_ORDER):
                    cur.execute(f"TRUNCATE TABLE `{table_name}`")
                cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()

        for table in TABLES:
            path = paths[table.name]
            variables = [f"@c{index}" for index, _ in enumerate(table.target_columns, start=1)]
            assignments = ", ".join(f"`{column}` = NULLIF({variable}, '')" for column, variable in zip(table.target_columns, variables))
            variable_list = ", ".join(variables)
            load_sql = f"""
LOAD DATA LOCAL INFILE %s
INTO TABLE `{table.name}`
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' ENCLOSED BY '"' ESCAPED BY '"'
LINES TERMINATED BY '\\n'
IGNORE 1 LINES
({variable_list})
SET {assignments}
"""
            log(f"Loading {path.name} into MariaDB table {table.name}...")
            with conn.cursor() as cur:
                cur.execute(load_sql, (str(path),))
            conn.commit()

        if not args.skip_indexes:
            with conn.cursor() as cur:
                log("Creating MariaDB indexes and statistics...")
                execute_mariadb_sql_file(cur, sql_file("mariadb", "02_indexes.sql"))
            conn.commit()
    finally:
        conn.close()


def main() -> int:
    args = parse_args()
    try:
        with materialized_source(args.source) as source:
            paths = validate_sources(source)
            if args.engine == "postgres":
                load_postgres(args, paths)
            else:
                load_mariadb(args, paths)
    except Exception as exc:
        print(f"pzero load failed: {exc}", file=sys.stderr)
        print(
            "Warning: the loader commits after each table to keep large CSV loads practical. "
            "If the failure happened after table loading began, the database may contain a partial load. "
            "Fix the issue and rerun with the default truncation behavior, or recreate the database.",
            file=sys.stderr,
        )
        return 1
    log("pzero load completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
