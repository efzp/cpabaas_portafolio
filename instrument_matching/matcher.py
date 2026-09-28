import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


CORPORATE_STOPWORDS = {
    "CORP",
    "CORPORATION",
    "INC",
    "INCORPORATED",
    "LTD",
    "LIMITED",
    "MGC",
    "PLC",
    "SA",
    "SAS",
}

SPECIAL_REVIEW_TICKERS = {
    "PFCIBEST": (
        "PFCIBEST participa en un cambio histórico de símbolo y requiere revisión."
    ),
}

EXCLUDED_TICKERS = {
    "PEI": (
        "PEI es un vehículo inmobiliario y no una empresa; se excluye del "
        "matching empresarial."
    ),
}

BUSINESS_SYMBOL_OVERRIDES = {
    "PFBCOLOM": {
        "providerSymbol": "CIBEST.CL",
        "reason": (
            "PFBCOLOM corresponde actualmente a CIBEST; regla de negocio "
            "validada."
        ),
    },
}

MARKET_ALIASES = {
    "NYSE": {"NYQ", "NYSE"},
    "NASDAQ": {"NAS", "NCM", "NGM", "NMS", "NASDAQ"},
    "BVC": {"BVC"},
}


@dataclass(frozen=True)
class QuerySpec:
    query: str
    reason: str
    symbol_weight: float


def canonical_text(value):
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", text.upper()).split())


def canonical_symbol(value):
    text = canonical_text(value).replace(" ", "-")
    return re.sub(r"-+", "-", text).strip("-")


def yahoo_underlying_symbol(value):
    text = str(value or "").strip().upper()
    if re.fullmatch(r"[A-Z0-9]+[./][A-Z]", text):
        return text.replace(".", "-").replace("/", "-")
    return text


def _add_query(specs, query, reason, symbol_weight):
    query = str(query or "").strip()
    if not query:
        return
    canonical_query = canonical_text(query)
    if any(canonical_text(item.query) == canonical_query for item in specs):
        return
    specs.append(QuerySpec(query, reason, symbol_weight))


def _meaningful_names(instrument):
    ticker = canonical_symbol(instrument.get("TickerNegociacion"))
    names = []
    for field in ("NombreEmpresa", "NombreInstrumento"):
        value = instrument.get(field)
        if not value:
            continue
        canonical_name = canonical_symbol(value)
        if canonical_name == ticker:
            continue
        if value not in names:
            names.append(value)
    return names


def build_query_plan(instrument):
    ticker = str(instrument.get("TickerNegociacion") or "").strip().upper()
    underlying = str(instrument.get("TickerSubyacente") or "").strip().upper()
    specs = []

    override = BUSINESS_SYMBOL_OVERRIDES.get(ticker)
    if override:
        return [
            QuerySpec(
                override["providerSymbol"],
                "REGLA_NEGOCIO",
                0.85,
            )
        ]

    if underlying:
        _add_query(
            specs,
            yahoo_underlying_symbol(underlying),
            "TICKER_SUBYACENTE",
            0.60,
        )

    _add_query(specs, ticker, "TICKER_NEGOCIACION", 0.45)

    if ticker and "." not in ticker and "-" not in ticker:
        _add_query(specs, f"{ticker}.CL", "SIMBOLO_BVC", 0.50)

    if ticker.endswith("CO") and len(ticker) > 4:
        _add_query(specs, ticker[:-2], "HEURISTICA_MGC_CO", 0.30)

    for name in _meaningful_names(instrument):
        _add_query(specs, name, "NOMBRE", 0.0)

    return specs


def _normalized_name(value):
    tokens = [
        token
        for token in canonical_text(value).split()
        if token not in CORPORATE_STOPWORDS
    ]
    return " ".join(tokens)


def name_similarity(instrument, quote):
    source_names = _meaningful_names(instrument)
    quote_names = [quote.get("longName"), quote.get("shortName")]
    best = 0.0
    for source_name in source_names:
        left = _normalized_name(source_name)
        if not left:
            continue
        for quote_name in quote_names:
            right = _normalized_name(quote_name)
            if not right:
                continue
            sequence_score = SequenceMatcher(None, left, right).ratio()
            left_tokens = set(left.split())
            right_tokens = set(right.split())
            token_score = len(left_tokens & right_tokens) / max(
                len(left_tokens | right_tokens), 1
            )
            best = max(best, sequence_score, token_score)
    return best


def _exchange_score(instrument, quote, symbol_reason):
    exchange_values = {
        canonical_text(quote.get("exchange")),
        canonical_text(quote.get("exchangeDisplay")),
    }
    origin = canonical_text(instrument.get("MercadoOrigen"))
    if origin:
        accepted = MARKET_ALIASES.get(origin, {origin})
        if exchange_values & accepted:
            return 0.10, True
        return 0.0, False
    if symbol_reason == "SIMBOLO_BVC" and "BVC" in exchange_values:
        return 0.10, True
    return 0.0, False


def score_candidate(instrument, quote, query_plan):
    candidate_symbol = canonical_symbol(quote.get("symbol"))
    matched_spec = None
    for spec in query_plan:
        if canonical_symbol(spec.query) != candidate_symbol:
            continue
        if matched_spec is None or spec.symbol_weight > matched_spec.symbol_weight:
            matched_spec = spec

    symbol_score = matched_spec.symbol_weight if matched_spec else 0.0
    symbol_reason = matched_spec.reason if matched_spec else None
    similarity = name_similarity(instrument, quote)
    name_score = round(similarity * 0.25, 5)
    exchange_score, exchange_match = _exchange_score(
        instrument,
        quote,
        symbol_reason,
    )
    type_score = 0.05 if quote.get("quoteType") == "EQUITY" else 0.02
    score = round(min(symbol_score + name_score + exchange_score + type_score, 1.0), 5)

    strong_identity = symbol_reason in {
        "TICKER_SUBYACENTE",
        "REGLA_NEGOCIO",
    } or similarity >= 0.80
    return {
        **quote,
        "score": score,
        "strongIdentity": strong_identity,
        "evidence": {
            "symbolReason": symbol_reason,
            "symbolScore": symbol_score,
            "nameSimilarity": round(similarity, 5),
            "nameScore": name_score,
            "exchangeMatch": exchange_match,
            "exchangeScore": exchange_score,
            "typeScore": type_score,
        },
    }


def _collect_quotes(client, query_plan, max_results):
    quotes_by_symbol = {}
    provider_errors = []
    for spec in query_plan:
        try:
            quotes = client.search(spec.query, max_results=max_results)
        except Exception as error:
            provider_errors.append(
                {"query": spec.query, "errorType": type(error).__name__}
            )
            continue

        for quote in quotes:
            key = canonical_symbol(quote.get("symbol"))
            if not key:
                continue
            if key not in quotes_by_symbol:
                quotes_by_symbol[key] = {**quote, "foundBy": []}
            if spec.query not in quotes_by_symbol[key]["foundBy"]:
                quotes_by_symbol[key]["foundBy"].append(spec.query)
    return list(quotes_by_symbol.values()), provider_errors


def match_instrument(
    instrument,
    client,
    max_results=8,
    automatic_threshold=0.85,
    ambiguity_margin=0.15,
):
    ticker = str(instrument.get("TickerNegociacion") or "").strip().upper()
    excluded_reason = EXCLUDED_TICKERS.get(ticker)
    if excluded_reason:
        return {
            "instrumentoId": instrument.get("InstrumentoID"),
            "tickerNegociacion": instrument.get("TickerNegociacion"),
            "tickerSubyacente": instrument.get("TickerSubyacente"),
            "nombreInstrumento": instrument.get("NombreInstrumento"),
            "nombreEmpresa": instrument.get("NombreEmpresa"),
            "decision": "EXCLUIDO",
            "reason": excluded_reason,
            "scoreMargin": 0.0,
            "queries": [],
            "topCandidate": None,
            "candidates": [],
            "providerErrors": [],
        }

    query_plan = build_query_plan(instrument)
    quotes, provider_errors = _collect_quotes(client, query_plan, max_results)
    candidates = [score_candidate(instrument, quote, query_plan) for quote in quotes]
    candidates.sort(key=lambda candidate: (-candidate["score"], candidate["symbol"]))
    candidates = candidates[:5]

    override = BUSINESS_SYMBOL_OVERRIDES.get(ticker)
    forced_review_reason = SPECIAL_REVIEW_TICKERS.get(ticker)
    top_candidate = candidates[0] if candidates else None
    second_score = candidates[1]["score"] if len(candidates) > 1 else 0.0
    score_margin = round(
        (top_candidate["score"] if top_candidate else 0.0) - second_score,
        5,
    )

    if top_candidate is None:
        if provider_errors and len(provider_errors) == len(query_plan):
            decision = "ERROR"
            reason = "Todas las consultas al proveedor fallaron."
        else:
            decision = "SIN_MATCH"
            reason = "Yahoo no devolvió candidatos compatibles."
    elif (
        override
        and canonical_symbol(top_candidate.get("symbol"))
        == canonical_symbol(override["providerSymbol"])
    ):
        decision = "VALIDADO"
        reason = override["reason"]
    elif forced_review_reason:
        decision = "REVISAR"
        reason = forced_review_reason
    elif not top_candidate["strongIdentity"]:
        decision = "REVISAR"
        reason = "Falta evidencia de identidad además de la coincidencia de símbolo."
    elif top_candidate["score"] < automatic_threshold:
        decision = "REVISAR"
        reason = "El mejor candidato no alcanza el umbral automático."
    elif score_margin < ambiguity_margin:
        decision = "REVISAR"
        reason = "La diferencia entre los dos mejores candidatos es ambigua."
    else:
        decision = "AUTOMATICO"
        reason = "Símbolo, identidad y margen superan los umbrales configurados."

    return {
        "instrumentoId": instrument.get("InstrumentoID"),
        "tickerNegociacion": instrument.get("TickerNegociacion"),
        "tickerSubyacente": instrument.get("TickerSubyacente"),
        "nombreInstrumento": instrument.get("NombreInstrumento"),
        "nombreEmpresa": instrument.get("NombreEmpresa"),
        "decision": decision,
        "reason": reason,
        "scoreMargin": score_margin,
        "queries": [spec.query for spec in query_plan],
        "topCandidate": top_candidate,
        "candidates": candidates,
        "providerErrors": provider_errors,
    }
