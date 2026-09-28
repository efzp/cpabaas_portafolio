SUPPORTED_QUOTE_TYPES = {"EQUITY", "ETF", "MUTUALFUND"}


class YahooSearchClient:
    """Adaptador mínimo para la búsqueda pública y configurable de Yahoo."""

    def __init__(self, base_url, timeout_seconds=15.0, session=None):
        if session is None:
            import requests

            session = requests.Session()
            self._owns_session = True
        else:
            self._owns_session = False

        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.session = session

    def search(self, query, max_results=8):
        response = self.session.get(
            self.base_url,
            params={
                "q": query,
                "quotesCount": max_results,
                "newsCount": 0,
                "listsCount": 0,
                "enableFuzzyQuery": "false",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; CPABAAS-Instrument-Matcher/1.0)",
                "Accept": "application/json",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        quotes = []
        for quote in payload.get("quotes", []):
            symbol = quote.get("symbol")
            quote_type = (quote.get("quoteType") or "").upper()
            if not symbol or quote_type not in SUPPORTED_QUOTE_TYPES:
                continue
            quotes.append(
                {
                    "symbol": symbol,
                    "shortName": quote.get("shortname"),
                    "longName": quote.get("longname"),
                    "exchange": quote.get("exchange"),
                    "exchangeDisplay": quote.get("exchDisp"),
                    "quoteType": quote_type,
                    "typeDisplay": quote.get("typeDisp"),
                }
            )
        return quotes

    def close(self):
        if self._owns_session:
            self.session.close()

