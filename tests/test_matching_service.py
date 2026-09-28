import unittest
from unittest.mock import patch

from instrument_matching.service import run_yahoo_matching_dry_run
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
        self.assertEqual(0, connection.commit_count)
        self.assertTrue(connection.closed)
        statements = [item[0] for item in connection._cursor.executions]
        self.assertTrue(all("sp_UpsertInstrumentoFuente" not in item for item in statements))


if __name__ == "__main__":
    unittest.main()

