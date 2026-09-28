import unittest
from unittest.mock import patch

from bvc_mgc.service import get_filename, run_bvc_load
from shared.config import BvcMgcSettings


class FakeResponse:
    def __init__(self, content, headers=None):
        self.content = content
        self.headers = headers or {}
        self.raise_called = False

    def raise_for_status(self):
        self.raise_called = True


class FakeCursor:
    def __init__(self, fetch_results):
        self.fetch_results = list(fetch_results)
        self.executions = []

    def execute(self, statement, *parameters):
        self.executions.append((statement, parameters))

    def fetchone(self):
        return self.fetch_results.pop(0)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.settings = BvcMgcSettings(
            page_url="https://example.test/page",
            file_url="https://example.test/file.xlsx",
            sql_connection_string="Authentication=ActiveDirectoryMsi;",
        )

    def test_get_filename_uses_header_or_default(self):
        response = FakeResponse(
            b"",
            {"Content-Disposition": 'attachment; filename="catalogo.xlsx"'},
        )
        self.assertEqual("catalogo.xlsx", get_filename(response))
        self.assertEqual("Valores_listados_MGC.xlsx", get_filename(FakeResponse(b"")))

    def test_rejects_non_xlsx_response_before_opening_sql(self):
        response = FakeResponse(b"contenido no valido")

        with (
            patch(
                "bvc_mgc.service.BvcMgcSettings.from_environment",
                return_value=self.settings,
            ),
            patch("bvc_mgc.service.download_mgc_file", return_value=response),
            patch("bvc_mgc.service.connect_sql") as connect_sql,
        ):
            with self.assertRaisesRegex(ValueError, "no parece ser un archivo XLSX"):
                run_bvc_load()

        self.assertTrue(response.raise_called)
        connect_sql.assert_not_called()

    def test_records_unchanged_file_and_closes_connection(self):
        response = FakeResponse(
            b"PK" + (b"x" * 1000),
            {
                "Content-Disposition": 'attachment; filename="catalogo.xlsx"',
                "ETag": "etag-1",
                "Last-Modified": "fecha-1",
            },
        )
        cursor = FakeCursor(fetch_results=[(134, 134, 0)])
        connection = FakeConnection(cursor)
        rows = [{"is_valid": True}]

        with (
            patch(
                "bvc_mgc.service.BvcMgcSettings.from_environment",
                return_value=self.settings,
            ),
            patch("bvc_mgc.service.download_mgc_file", return_value=response),
            patch(
                "bvc_mgc.service.extract_mgc_rows",
                return_value=(rows, "Valores"),
            ),
            patch("bvc_mgc.service.connect_sql", return_value=connection),
        ):
            result = run_bvc_load()

        self.assertEqual("SIN_CAMBIOS", result["status"])
        self.assertEqual("catalogo.xlsx", result["file"])
        self.assertEqual(1, connection.commit_count)
        self.assertTrue(connection.closed)
        self.assertTrue(
            any("SIN_CAMBIOS" in statement for statement, _ in cursor.executions)
        )

    def test_processes_new_file_and_updates_catalog(self):
        response = FakeResponse(b"PK" + (b"x" * 1000))
        cursor = FakeCursor(fetch_results=[None, (42,), (1,)])
        connection = FakeConnection(cursor)
        rows = [{"is_valid": True}]

        with (
            patch(
                "bvc_mgc.service.BvcMgcSettings.from_environment",
                return_value=self.settings,
            ),
            patch("bvc_mgc.service.download_mgc_file", return_value=response),
            patch(
                "bvc_mgc.service.extract_mgc_rows",
                return_value=(rows, "Valores"),
            ),
            patch("bvc_mgc.service.connect_sql", return_value=connection),
            patch("bvc_mgc.service.insert_stage_rows") as insert_stage_rows,
            patch("bvc_mgc.service.upsert_catalog") as upsert_catalog,
        ):
            result = run_bvc_load()

        self.assertEqual(
            {
                "status": "OK",
                "load_id": 42,
                "file": "Valores_listados_MGC.xlsx",
                "sheet": "Valores",
                "total": 1,
                "valid": 1,
                "rejected": 0,
            },
            result,
        )
        insert_stage_rows.assert_called_once_with(cursor, 42, rows)
        upsert_catalog.assert_called_once_with(cursor, 42, rows)
        self.assertEqual(2, connection.commit_count)
        self.assertTrue(connection.closed)

    def test_requires_review_when_valid_rows_drop_more_than_twenty_percent(self):
        response = FakeResponse(b"PK" + (b"x" * 1000))
        cursor = FakeCursor(fetch_results=[None, (43,), (10,)])
        connection = FakeConnection(cursor)
        rows = [{"is_valid": True}]

        with (
            patch(
                "bvc_mgc.service.BvcMgcSettings.from_environment",
                return_value=self.settings,
            ),
            patch("bvc_mgc.service.download_mgc_file", return_value=response),
            patch(
                "bvc_mgc.service.extract_mgc_rows",
                return_value=(rows, "Valores"),
            ),
            patch("bvc_mgc.service.connect_sql", return_value=connection),
            patch("bvc_mgc.service.insert_stage_rows") as insert_stage_rows,
            patch("bvc_mgc.service.upsert_catalog") as upsert_catalog,
        ):
            result = run_bvc_load()

        self.assertEqual(
            {
                "status": "REQUIERE_REVISION",
                "load_id": 43,
                "total": 1,
                "valid": 1,
            },
            result,
        )
        insert_stage_rows.assert_called_once_with(cursor, 43, rows)
        upsert_catalog.assert_not_called()
        self.assertEqual(2, connection.commit_count)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
