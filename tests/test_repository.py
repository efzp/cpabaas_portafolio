import unittest

from bvc_mgc.repository import insert_stage_rows, upsert_catalog


def make_row(nemo, is_valid=True):
    return {
        "row_number": 2,
        "nemo": nemo,
        "name": f"Nombre {nemo}",
        "isin": None,
        "issuer": "Emisor",
        "issuer_id": None,
        "description": None,
        "investor_url": None,
        "regulator_url": None,
        "underlying_market_source": None,
        "security_type_source": None,
        "country": None,
        "sponsor": None,
        "sponsor_nit": None,
        "is_valid": is_valid,
        "validation_message": None if is_valid else "Error",
    }


class FakeCursor:
    def __init__(self, fetch_results=None):
        self.fetch_results = list(fetch_results or [])
        self.executions = []
        self.executemany_call = None

    def execute(self, statement, *parameters):
        self.executions.append((statement, parameters))

    def executemany(self, statement, parameters):
        self.executemany_call = (statement, parameters)

    def fetchone(self):
        return self.fetch_results.pop(0)


class RepositoryTests(unittest.TestCase):
    def test_maps_stage_parameters_without_changing_validation(self):
        cursor = FakeCursor()

        insert_stage_rows(cursor, 42, [make_row("ABC"), make_row("BAD", False)])

        statement, parameters = cursor.executemany_call
        self.assertIn("INSERT INTO dbo.BvcMgcValorStage", statement)
        self.assertEqual(2, len(parameters))
        self.assertEqual(42, parameters[0][0])
        self.assertEqual("ABC", parameters[0][2])
        self.assertEqual(1, parameters[0][-2])
        self.assertEqual(0, parameters[1][-2])
        self.assertEqual("Error", parameters[1][-1])

    def test_updates_existing_and_inserts_new_valid_rows(self):
        cursor = FakeCursor(fetch_results=[(100,), None])
        rows = [make_row("EXISTE"), make_row("NUEVO"), make_row("INVALIDO", False)]

        upsert_catalog(cursor, 7, rows)

        statements = [statement for statement, _ in cursor.executions]
        self.assertEqual(5, len(statements))
        self.assertIn("UPDATE catalog", statements[0])
        self.assertIn("SELECT BvcMgcValorID", statements[1])
        self.assertIn("UPDATE dbo.BvcMgcValor", statements[2])
        self.assertIn("SELECT BvcMgcValorID", statements[3])
        self.assertIn("INSERT INTO dbo.BvcMgcValor", statements[4])


if __name__ == "__main__":
    unittest.main()
