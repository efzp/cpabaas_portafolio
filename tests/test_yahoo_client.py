import unittest

from instrument_matching.client import YahooSearchClient


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "quotes": [
                {
                    "symbol": "PEI.CL",
                    "shortname": "PATRIMONIO AUTONOMO",
                    "longname": "Patrimonio Autónomo Estrategias Inmobiliarias",
                    "exchange": "BVC",
                    "exchDisp": "BVC",
                    "quoteType": "EQUITY",
                    "typeDisp": "Equity",
                },
                {
                    "symbol": "PEI260101C00010000",
                    "quoteType": "OPTION",
                },
            ]
        }


class FakeSession:
    def __init__(self):
        self.calls = []
        self.closed = False

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse()

    def close(self):
        self.closed = True


class YahooClientTests(unittest.TestCase):
    def test_maps_supported_quotes_and_filters_options(self):
        session = FakeSession()
        client = YahooSearchClient(
            "https://example.test/search",
            timeout_seconds=7,
            session=session,
        )

        result = client.search("PEI", max_results=5)

        self.assertEqual(1, len(result))
        self.assertEqual("PEI.CL", result[0]["symbol"])
        _, kwargs = session.calls[0]
        self.assertEqual("PEI", kwargs["params"]["q"])
        self.assertEqual(5, kwargs["params"]["quotesCount"])
        self.assertEqual(7, kwargs["timeout"])


if __name__ == "__main__":
    unittest.main()

