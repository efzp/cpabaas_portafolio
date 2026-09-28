import os
import unittest
from unittest.mock import patch

from shared.config import BvcMgcSettings


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


if __name__ == "__main__":
    unittest.main()
