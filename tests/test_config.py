import os
import unittest
from unittest.mock import patch

from shared.config import BvcMgcSettings, YahooMatchSettings


class BvcMgcSettingsTests(unittest.TestCase):
    def test_reads_required_values_from_environment(self):
        values = {
            "BVC_MGC_PAGE_URL": "https://example.test/page",
            "BVC_MGC_FILE_URL": "https://example.test/file.xlsx",
            "SQL_CONNECTION_STRING": "Authentication=ActiveDirectoryMsi;",
        }

        with patch.dict(os.environ, values, clear=True):
            settings = BvcMgcSettings.from_environment()

        self.assertEqual(values["BVC_MGC_PAGE_URL"], settings.page_url)
        self.assertEqual(values["BVC_MGC_FILE_URL"], settings.file_url)
        self.assertEqual(
            values["SQL_CONNECTION_STRING"], settings.sql_connection_string
        )

    def test_missing_required_value_raises_key_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(KeyError):
                BvcMgcSettings.from_environment()


class YahooMatchSettingsTests(unittest.TestCase):
    def test_reads_defaults_and_required_sql_connection(self):
        with patch.dict(
            os.environ,
            {"SQL_CONNECTION_STRING": "Authentication=ActiveDirectoryMsi;"},
            clear=True,
        ):
            settings = YahooMatchSettings.from_environment()

        self.assertEqual(8, settings.max_results)
        self.assertEqual(0.85, settings.automatic_threshold)
        self.assertEqual(0.15, settings.ambiguity_margin)

    def test_rejects_invalid_threshold(self):
        with patch.dict(
            os.environ,
            {
                "SQL_CONNECTION_STRING": "Authentication=ActiveDirectoryMsi;",
                "YAHOO_MATCH_AUTOMATIC_THRESHOLD": "1.5",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "entre 0 y 1"):
                YahooMatchSettings.from_environment()


if __name__ == "__main__":
    unittest.main()
