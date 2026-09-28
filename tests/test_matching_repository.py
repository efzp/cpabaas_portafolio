import unittest

from instrument_matching.repository import (
    fetch_pending_instruments,
    upsert_instrument_source,
)


class FakeCursor:
    def __init__(self):
        self.description = [
            ("InstrumentoID",),
            ("TickerNegociacion",),
            ("NombreInstrumento",),
        ]
        self.executions = []

    def execute(self, statement, *parameters):
        self.executions.append((statement, parameters))

    def fetchall(self):
        return [(2, "BRKB", "Berkshire Hathaway - MGC")]


class MatchingRepositoryTests(unittest.TestCase):
    def test_reads_only_through_pending_instruments_procedure(self):
        cursor = FakeCursor()

        result = fetch_pending_instruments(cursor, source="YAHOO")

        self.assertEqual(
            [
                {
                    "InstrumentoID": 2,
                    "TickerNegociacion": "BRKB",
                    "NombreInstrumento": "Berkshire Hathaway - MGC",
                }
            ],
            result,
        )
        statement, parameters = cursor.executions[0]
        self.assertIn("dbo.sp_InstrumentosPendientesFuente", statement)
        self.assertNotIn("InstrumentoFuente", statement)
        self.assertEqual(("YAHOO",), parameters)

    def test_upserts_accepted_match_through_stored_procedure(self):
        cursor = FakeCursor()
        match = {
            "instrumentoId": 42,
            "decision": "VALIDADO",
            "topCandidate": {
                "symbol": "GOOGL",
                "longName": "Alphabet Inc.",
                "shortName": "Alphabet",
                "exchange": "NMS",
                "exchangeDisplay": "NASDAQ",
                "currency": "USD",
                "quoteType": "EQUITY",
                "score": 0.50,
            },
        }

        upsert_instrument_source(cursor, match)

        statement, parameters = cursor.executions[0]
        self.assertIn("dbo.sp_UpsertInstrumentoFuente", statement)
        self.assertEqual(
            (
                42,
                "YAHOO",
                "GOOGL",
                "Alphabet Inc.",
                "NASDAQ",
                "USD",
                "EQUITY",
                "VALIDADO",
                0.50,
            ),
            parameters,
        )

    def test_rejects_non_writable_match(self):
        cursor = FakeCursor()

        with self.assertRaisesRegex(ValueError, "matches aceptados"):
            upsert_instrument_source(
                cursor,
                {
                    "instrumentoId": 28,
                    "decision": "EXCLUIDO",
                    "topCandidate": None,
                },
            )

        self.assertEqual([], cursor.executions)


if __name__ == "__main__":
    unittest.main()
