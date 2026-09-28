import unittest
from unittest.mock import patch

from instrument_matching.service import (
    run_yahoo_matching_apply,
    run_yahoo_matching_dry_run,
)
from shared.config import YahooMatchSettings


class FakeCursor:
    description = [
        ("InstrumentoID",),
        ("NombreInstrumento",),
        ("TickerNegociacion",),
        ("TickerSubyacente",),
        ("MercadoOrigen",),
        ("NombreEmpresa",),
    ]

    def __init__(self):
        self.executions = []

    def execute(self, statement, *parameters):
        self.executions.append((statement, parameters))

    def fetchall(self):
        return [
            (
                2,
                "Berkshire Hathaway - MGC",
                "BRKB",
                "BRK.B",
                "NYSE",
                "Berkshire Hathaway Inc.",
            )
        ]


class FakeConnection:
    def __init__(self):
        self._cursor = FakeCursor()
        self.closed = False
        self.commit_count = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commit_count += 1
        raise AssertionError("El dry-run no debe hacer commit.")

    def close(self):
        self.closed = True


class ApplyConnection:
    def __init__(self, fail_upsert=False):
        self._cursor = FakeCursor()
        self.closed = False
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_upsert = fail_upsert
        original_execute = self._cursor.execute

        def execute(statement, *parameters):
            if fail_upsert and "sp_UpsertInstrumentoFuente" in statement:
                raise RuntimeError("simulated upsert failure")
            original_execute(statement, *parameters)

        self._cursor.execute = execute

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


class FakeClient:
    def search(self, query, max_results=8):
        if query != "BRK-B":
            return []
        return [
            {
                "symbol": "BRK-B",
                "shortName": "Berkshire Hathaway Inc.",
                "longName": "Berkshire Hathaway Inc.",
                "exchange": "NYSE",
                "exchangeDisplay": "NYSE",
                "quoteType": "EQUITY",
                "typeDisplay": "Equity",
            }
        ]


class MatchingServiceTests(unittest.TestCase):
    def test_dry_run_closes_connection_and_never_commits(self):
        settings = YahooMatchSettings(
            sql_connection_string="Authentication=ActiveDirectoryMsi;"
        )
        connection = FakeConnection()

        with patch(
            "instrument_matching.service.connect_sql",
            return_value=connection,
        ):
            result = run_yahoo_matching_dry_run(settings, client=FakeClient())

        self.assertEqual("DRY_RUN", result["mode"])
        self.assertEqual(0, result["writesPerformed"])
        self.assertEqual(1, result["summary"]["automatico"])
        self.assertEqual(0, result["summary"]["validado"])
        self.assertEqual(0, result["summary"]["excluido"])
        self.assertEqual(0, connection.commit_count)
        self.assertTrue(connection.closed)
        statements = [item[0] for item in connection._cursor.executions]
        self.assertTrue(all("sp_UpsertInstrumentoFuente" not in item for item in statements))

    def test_apply_commits_accepted_matches_through_upsert_procedure(self):
        settings = YahooMatchSettings(
            sql_connection_string="Authentication=ActiveDirectoryMsi;"
        )
        connection = ApplyConnection()

        with patch(
            "instrument_matching.service.connect_sql",
            return_value=connection,
        ):
            result = run_yahoo_matching_apply(settings, client=FakeClient())

        self.assertEqual("APPLY", result["mode"])
        self.assertEqual(1, result["writesPerformed"])
        self.assertTrue(result["committed"])
        self.assertTrue(result["results"][0]["writeApplied"])
        self.assertEqual(1, connection.commit_count)
        self.assertEqual(0, connection.rollback_count)
        self.assertTrue(connection.closed)
        statements = [item[0] for item in connection._cursor.executions]
        self.assertEqual(
            1,
            sum("sp_UpsertInstrumentoFuente" in item for item in statements),
        )

    def test_apply_rolls_back_and_closes_connection_when_upsert_fails(self):
        settings = YahooMatchSettings(
            sql_connection_string="Authentication=ActiveDirectoryMsi;"
        )
        connection = ApplyConnection(fail_upsert=True)

        with patch(
            "instrument_matching.service.connect_sql",
            return_value=connection,
        ):
            with self.assertRaisesRegex(RuntimeError, "upsert failure"):
                run_yahoo_matching_apply(settings, client=FakeClient())

        self.assertEqual(0, connection.commit_count)
        self.assertEqual(1, connection.rollback_count)
        self.assertTrue(connection.closed)

    def test_apply_skips_excluded_results(self):
        settings = YahooMatchSettings(
            sql_connection_string="Authentication=ActiveDirectoryMsi;"
        )
        connection = ApplyConnection()
        results = [
            {
                "instrumentoId": 42,
                "decision": "VALIDADO",
                "topCandidate": {
                    "symbol": "GOOGL",
                    "longName": "Alphabet Inc.",
                    "exchange": "NMS",
                    "quoteType": "EQUITY",
                    "score": 0.50,
                },
            },
            {
                "instrumentoId": 28,
                "decision": "EXCLUIDO",
                "topCandidate": None,
            },
        ]

        with (
            patch(
                "instrument_matching.service.connect_sql",
                return_value=connection,
            ),
            patch(
                "instrument_matching.service._match_pending_instruments",
                return_value=results,
            ),
        ):
            result = run_yahoo_matching_apply(settings, client=FakeClient())

        self.assertEqual(1, result["writesPerformed"])
        self.assertTrue(result["results"][0]["writeApplied"])
        self.assertFalse(result["results"][1]["writeApplied"])
        statements = [item[0] for item in connection._cursor.executions]
        self.assertEqual(
            1,
            sum("sp_UpsertInstrumentoFuente" in item for item in statements),
        )


if __name__ == "__main__":
    unittest.main()
