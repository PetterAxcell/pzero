from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "pzero_load.py"

spec = importlib.util.spec_from_file_location("pzero_load", MODULE_PATH)
pzero_load = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pzero_load
assert spec.loader is not None
spec.loader.exec_module(pzero_load)


def csv_text(table) -> str:
    return ",".join(table.source_columns) + "\n"


def write_all_csvs(root: Path, *, demographics_filename: str = "demographic.csv") -> None:
    for table in pzero_load.TABLES:
        filename = demographics_filename if table.name == "demographics" else table.filenames[0]
        (root / filename).write_text(csv_text(table), encoding="utf-8")


def write_zip(zip_path: Path, *, demographics_filename: str = "demographic.csv") -> None:
    with zipfile.ZipFile(zip_path, "w") as archive:
        for table in pzero_load.TABLES:
            filename = demographics_filename if table.name == "demographics" else table.filenames[0]
            archive.writestr(filename, csv_text(table))


class PzeroLoaderTests(unittest.TestCase):
    def test_directory_source_resolves_extracted_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_all_csvs(root)

            with pzero_load.materialized_source(str(root)) as source:
                paths = pzero_load.validate_sources(source)

            self.assertEqual(set(paths), {table.name for table in pzero_load.TABLES})
            self.assertEqual(paths["demographics"].name, "demographic.csv")

    def test_directory_source_autodetects_single_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_zip(root / "csvs_P0.zip")

            with pzero_load.materialized_source(str(root)) as source:
                paths = pzero_load.validate_sources(source)

            self.assertEqual(paths["ward_stays"].name, "ward_stays.csv")

    def test_demographics_plural_alias_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_all_csvs(root, demographics_filename="demographics.csv")

            with pzero_load.materialized_source(str(root)) as source:
                paths = pzero_load.validate_sources(source)

            self.assertEqual(paths["demographics"].name, "demographics.csv")

    def test_header_validation_rejects_reordered_columns(self) -> None:
        table = pzero_load.table_by_name("labs")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "labs.csv"
            path.write_text("lab_sap_ref,stay_id,result_num,result_txt,extract_date\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Expected exact order"):
                pzero_load.validate_csv_header(table, path)

    def test_split_sql_statements(self) -> None:
        sql_text = """
        -- ignored comment
        CREATE TABLE one (id INT);

        CREATE INDEX idx_one_id
        ON one (id);
        """

        self.assertEqual(
            pzero_load.split_sql_statements(sql_text),
            ["CREATE TABLE one (id INT)", "CREATE INDEX idx_one_id\n        ON one (id)"],
        )


if __name__ == "__main__":
    unittest.main()

