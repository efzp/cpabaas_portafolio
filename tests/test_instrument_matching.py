import unittest

from instrument_matching.matcher import (
    build_query_plan,
    canonical_symbol,
    canonical_text,
    match_instrument,
)


def make_instrument(**overrides):
    instrument = {
        "InstrumentoID": 1,
        "EmpresaID": None,
        "NombreInstrumento": "ABC",
        "TickerNegociacion": "ABC",
        "MercadoNegociacion": "POR_CLASIFICAR",
        "MonedaNegociacion": "COP",
        "TickerSubyacente": None,
        "MercadoOrigen": None,
        "MonedaSubyacente": None,
        "ISIN": None,
        "NombreEmpresa": None,
    }
    instrument.update(overrides)
    return instrument


def make_quote(symbol, name, exchange="BVC", quote_type="EQUITY"):
    return {
        "symbol": symbol,
        "shortName": name,
        "longName": name,
        "exchange": exchange,
        "exchangeDisplay": exchange,
        "quoteType": quote_type,
        "typeDisplay": quote_type.title(),
    }


class FakeClient:
    def __init__(self, responses=None, errors=None):
        self.responses = responses or {}
        self.errors = errors or set()
        self.calls = []

    def search(self, query, max_results=8):
        self.calls.append((query, max_results))
        if query in self.errors:
            raise TimeoutError("simulated")
        return self.responses.get(query, [])


class InstrumentMatchingTests(unittest.TestCase):
    def test_canonicalizes_accents_and_share_class_symbols(self):
        self.assertEqual("PATRIMONIO AUTONOMO", canonical_text("Patrimonio Autónomo"))
        self.assertEqual(canonical_symbol("BRK.B"), canonical_symbol("brk-b"))

    def test_builds_underlying_mgc_and_business_override_queries(self):
        berkshire = make_instrument(
            TickerNegociacion="BRKB",
            TickerSubyacente="BRK.B",
            NombreEmpresa="Berkshire Hathaway Inc.",
        )
        self.assertEqual("BRK-B", build_query_plan(berkshire)[0].query)

        microsoft = make_instrument(TickerNegociacion="MSFTCO")
        microsoft_queries = [item.query for item in build_query_plan(microsoft)]
        self.assertIn("MSFTCO.CL", microsoft_queries)
        self.assertIn("MSFT", microsoft_queries)

        historical = make_instrument(TickerNegociacion="PFBCOLOM")
        historical_queries = [item.query for item in build_query_plan(historical)]
        self.assertEqual(["CIBEST.CL"], historical_queries)

    def test_accepts_strong_underlying_match_with_clear_margin(self):
        instrument = make_instrument(
            InstrumentoID=2,
            NombreInstrumento="Berkshire Hathaway - MGC",
            TickerNegociacion="BRKB",
            TickerSubyacente="BRK.B",
            MercadoOrigen="NYSE",
            NombreEmpresa="Berkshire Hathaway Inc.",
        )
        client = FakeClient(
            {
                "BRK-B": [
                    make_quote(
                        "BRK-B",
                        "Berkshire Hathaway Inc.",
                        exchange="NYSE",
                    ),
                    make_quote("BRK-A", "Berkshire Hathaway Inc.", exchange="NYSE"),
                ]
            }
        )

        result = match_instrument(instrument, client)

        self.assertEqual("AUTOMATICO", result["decision"])
        self.assertEqual("BRK-B", result["topCandidate"]["symbol"])
        self.assertTrue(result["topCandidate"]["strongIdentity"])
        self.assertGreaterEqual(result["scoreMargin"], 0.15)

    def test_excludes_pei_without_calling_provider(self):
        instrument = make_instrument(
            InstrumentoID=28,
            NombreInstrumento="PEI",
            TickerNegociacion="PEI",
        )
        client = FakeClient(
            {
                "PEI": [
                    make_quote("PEIYX", "Putnam Large Cap Value", "NASDAQ", "MUTUALFUND"),
                    make_quote(
                        "PEI.CL",
                        "Patrimonio Autónomo Estrategias Inmobiliarias",
                    ),
                ]
            }
        )

        result = match_instrument(instrument, client)

        self.assertEqual("EXCLUIDO", result["decision"])
        self.assertIsNone(result["topCandidate"])
        self.assertEqual([], result["queries"])
        self.assertEqual([], client.calls)
        self.assertIn("no una empresa", result["reason"])

    def test_validates_pfbcolom_against_exact_cibest_symbol(self):
        instrument = make_instrument(
            InstrumentoID=46,
            NombreInstrumento="PFBCOLOM",
            TickerNegociacion="PFBCOLOM",
        )
        client = FakeClient(
            {
                "CIBEST.CL": [
                    make_quote("CIBEST.CL", "Grupo Cibest S.A.", "BVC")
                ]
            }
        )

        result = match_instrument(instrument, client)

        self.assertEqual("VALIDADO", result["decision"])
        self.assertEqual("CIBEST.CL", result["topCandidate"]["symbol"])
        self.assertEqual(
            "REGLA_NEGOCIO",
            result["topCandidate"]["evidence"]["symbolReason"],
        )
        self.assertEqual(["CIBEST.CL"], result["queries"])
        self.assertIn("regla de negocio", result["reason"])

    def test_validates_exact_bvc_symbol_after_removing_cl_suffix(self):
        instrument = make_instrument(
            InstrumentoID=24,
            NombreInstrumento="ECOPETROL",
            TickerNegociacion="ECOPETROL",
        )
        client = FakeClient(
            {
                "ECOPETROL.CL": [
                    make_quote("ECOPETROL.CL", "Ecopetrol S.A.", "BVC")
                ]
            }
        )

        result = match_instrument(instrument, client)

        self.assertEqual("VALIDADO", result["decision"])
        self.assertEqual("ECOPETROL.CL", result["topCandidate"]["symbol"])
        self.assertTrue(
            result["topCandidate"]["evidence"]["localSymbolMatch"]
        )
        self.assertIn("sufijo BVC .CL", result["reason"])

    def test_validates_exact_direct_symbol_as_fallback(self):
        instrument = make_instrument(
            InstrumentoID=42,
            NombreInstrumento="GOOGL",
            TickerNegociacion="GOOGL",
        )
        client = FakeClient(
            {"GOOGL": [make_quote("GOOGL", "Alphabet Inc.", "NASDAQ")]}
        )

        result = match_instrument(instrument, client)

        self.assertEqual("VALIDADO", result["decision"])
        self.assertEqual("GOOGL", result["topCandidate"]["symbol"])
        self.assertTrue(
            result["topCandidate"]["evidence"]["directSymbolMatch"]
        )
        self.assertIn("sin transformar sufijos", result["reason"])

    def test_direct_fallback_rejects_non_equity(self):
        instrument = make_instrument(
            NombreInstrumento="ABC",
            TickerNegociacion="ABC",
        )
        client = FakeClient(
            {"ABC": [make_quote("ABC", "ABC Fund", "NASDAQ", "MUTUALFUND")]}
        )

        result = match_instrument(instrument, client)

        self.assertEqual("REVISAR", result["decision"])
        self.assertFalse(
            result["topCandidate"]["evidence"]["directSymbolMatch"]
        )

    def test_marks_close_candidates_as_ambiguous(self):
        instrument = make_instrument(
            NombreInstrumento="Alpha Corporation",
            TickerNegociacion="ABC",
        )
        client = FakeClient(
            {
                "ABC": [
                    make_quote("ABC", "Alpha Corporation", "NYSE"),
                    make_quote("ABC.CL", "Alpha Corporation", "NYSE"),
                ]
            }
        )

        result = match_instrument(
            instrument,
            client,
            automatic_threshold=0.70,
            ambiguity_margin=0.16,
        )

        self.assertEqual("REVISAR", result["decision"])
        self.assertFalse(
            result["topCandidate"]["evidence"]["localSymbolMatch"]
        )
        self.assertIn("ambigua", result["reason"])

    def test_returns_no_match_when_provider_has_no_candidates(self):
        result = match_instrument(make_instrument(), FakeClient())

        self.assertEqual("SIN_MATCH", result["decision"])
        self.assertIsNone(result["topCandidate"])

    def test_records_provider_error_without_exposing_message(self):
        plan = build_query_plan(make_instrument())
        client = FakeClient(errors={item.query for item in plan})

        result = match_instrument(make_instrument(), client)

        self.assertEqual("ERROR", result["decision"])
        self.assertTrue(result["providerErrors"])
        self.assertEqual(
            {"query": "ABC", "errorType": "TimeoutError"},
            result["providerErrors"][0],
        )


if __name__ == "__main__":
    unittest.main()
