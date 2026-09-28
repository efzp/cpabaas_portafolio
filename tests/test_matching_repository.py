import unittest

from instrument_matching.repository import fetch_pending_instruments


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


if __name__ == "__main__":
    unittest.main()

