import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BvcMgcSettings:
    page_url: str
    file_url: str
    sql_connection_string: str

    @classmethod
    def from_environment(cls):
        return cls(
            page_url=os.environ["BVC_MGC_PAGE_URL"],
            file_url=os.environ["BVC_MGC_FILE_URL"],
            sql_connection_string=os.environ["SQL_CONNECTION_STRING"],
        )


@dataclass(frozen=True)
class YahooMatchSettings:
    sql_connection_string: str
    search_url: str = "https://query1.finance.yahoo.com/v1/finance/search"
    request_timeout_seconds: float = 15.0
    max_results: int = 8
    automatic_threshold: float = 0.85
    ambiguity_margin: float = 0.15

    @classmethod
    def from_environment(cls):
        settings = cls(
            sql_connection_string=os.environ["SQL_CONNECTION_STRING"],
            search_url=os.environ.get(
                "YAHOO_SEARCH_URL",
                "https://query1.finance.yahoo.com/v1/finance/search",
            ),
            request_timeout_seconds=float(
                os.environ.get("YAHOO_REQUEST_TIMEOUT_SECONDS", "15")
            ),
            max_results=int(os.environ.get("YAHOO_MATCH_MAX_RESULTS", "8")),
            automatic_threshold=float(
                os.environ.get("YAHOO_MATCH_AUTOMATIC_THRESHOLD", "0.85")
            ),
            ambiguity_margin=float(
                os.environ.get("YAHOO_MATCH_AMBIGUITY_MARGIN", "0.15")
            ),
        )
        if settings.request_timeout_seconds <= 0:
            raise ValueError("YAHOO_REQUEST_TIMEOUT_SECONDS debe ser positivo.")
        if settings.max_results < 1 or settings.max_results > 20:
            raise ValueError("YAHOO_MATCH_MAX_RESULTS debe estar entre 1 y 20.")
        if not 0 <= settings.automatic_threshold <= 1:
            raise ValueError(
                "YAHOO_MATCH_AUTOMATIC_THRESHOLD debe estar entre 0 y 1."
            )
        if not 0 <= settings.ambiguity_margin <= 1:
            raise ValueError("YAHOO_MATCH_AMBIGUITY_MARGIN debe estar entre 0 y 1.")
        return settings
