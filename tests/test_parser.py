import unittest
from unittest.mock import patch

from bvc_mgc.parser import (
    clean_value,
    extract_mgc_rows,
    normalize_header,
    valid_isin,
)


class FakeSheet:
    def __init__(self, title, rows):
        self.title = title
        self._rows = rows
        self.max_row = len(rows)

    def iter_rows(self, min_row, max_row=None, values_only=True):
        del values_only
        end = max_row if max_row is not None else len(self._rows)
        return iter(self._rows[min_row - 1 : end])


class FakeWorkbook:
    def __init__(self, worksheets):
        self.worksheets = worksheets


class ParserTests(unittest.TestCase):
    def test_normalizes_headers_and_excel_errors(self):
        self.assertEqual("LINKREGULADOR", normalize_header("Link regulador"))
        self.assertEqual("DESCRIPCION", normalize_header("Descripción"))
        self.assertIsNone(clean_value(" #N/A "))
        self.assertEqual("valor", clean_value(" valor "))

    def test_validates_and_normalizes_isin(self):
        self.assertEqual("CO0000000001", valid_isin("co 0000000001"))
        self.assertIsNone(valid_isin("ISIN INVALIDO"))

    def test_extracts_rows_and_marks_duplicates(self):
        sheet = FakeSheet(
            "Valores",
            [
                ("Reporte", None, None, None, None),
                ("Némo", "Nombre", "ISIN", "Emisor", "Descripción"),
                ("abc", "Activo A", "CO0000000001", "Emisor A", "Desc A"),
                ("dup", "Duplicado 1", None, "Emisor D", None),
                ("DUP", "Duplicado 2", "incorrecto", "Emisor D", None),
                (None, None, None, None, None),
            ],
        )

        with patch(
            "bvc_mgc.parser.load_mgc_workbook",
            return_value=FakeWorkbook([sheet]),
        ):
            rows, sheet_name = extract_mgc_rows(b"contenido")

        self.assertEqual("Valores", sheet_name)
        self.assertEqual(3, len(rows))
        self.assertEqual("ABC", rows[0]["nemo"])
        self.assertTrue(rows[0]["is_valid"])
        self.assertEqual("Desc A", rows[0]["description"])
        self.assertFalse(rows[1]["is_valid"])
        self.assertIn("NEMO duplicado", rows[1]["validation_message"])
        self.assertFalse(rows[2]["is_valid"])
        self.assertIn("ISIN descartado", rows[2]["validation_message"])

    def test_rejects_workbook_without_required_headers(self):
        sheet = FakeSheet("Hoja", [("NEMO", "NOMBRE")])

        with patch(
            "bvc_mgc.parser.load_mgc_workbook",
            return_value=FakeWorkbook([sheet]),
        ):
            with self.assertRaisesRegex(ValueError, "columnas NEMO"):
                extract_mgc_rows(b"contenido")


if __name__ == "__main__":
    unittest.main()
