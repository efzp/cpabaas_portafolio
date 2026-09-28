import json
import unittest
from unittest.mock import patch

import azure.functions as func

import function_app


def make_request(payload=None, raw_body=None):
    if raw_body is None:
        raw_body = json.dumps(payload).encode("utf-8")
    return func.HttpRequest(
        method="POST",
        url="http://localhost/api/instrumentos/matching/yahoo/apply",
        body=raw_body,
    )


class YahooMatchingApplyFunctionTests(unittest.TestCase):
    def test_rejects_missing_confirmation_without_running_service(self):
        with patch.object(function_app, "run_yahoo_matching_apply") as service:
            response = function_app.yahoo_matching_apply(make_request({}))

        self.assertEqual(400, response.status_code)
        self.assertEqual("REJECTED", json.loads(response.get_body())["status"])
        service.assert_not_called()

    def test_rejects_invalid_json_without_running_service(self):
        with patch.object(function_app, "run_yahoo_matching_apply") as service:
            response = function_app.yahoo_matching_apply(
                make_request(raw_body=b"not-json")
            )

        self.assertEqual(400, response.status_code)
        service.assert_not_called()

    def test_applies_matching_only_with_explicit_confirmation(self):
        expected = {
            "status": "OK",
            "mode": "APPLY",
            "writesPerformed": 10,
            "committed": True,
        }
        with patch.object(
            function_app,
            "run_yahoo_matching_apply",
            return_value=expected,
        ) as service:
            response = function_app.yahoo_matching_apply(
                make_request({"confirm": True})
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual(expected, json.loads(response.get_body()))
        service.assert_called_once_with()

    def test_returns_sanitized_error_when_apply_fails(self):
        with (
            patch.object(
                function_app,
                "run_yahoo_matching_apply",
                side_effect=RuntimeError("sensitive database details"),
            ),
            patch.object(function_app.logging, "exception"),
        ):
            response = function_app.yahoo_matching_apply(
                make_request({"confirm": True})
            )

        payload = json.loads(response.get_body())
        self.assertEqual(500, response.status_code)
        self.assertEqual("ERROR", payload["status"])
        self.assertFalse(payload["committed"])
        self.assertNotIn("sensitive", response.get_body().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
