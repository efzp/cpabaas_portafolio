import logging
from collections import Counter
from datetime import datetime, timezone

from instrument_matching.client import YahooSearchClient
from instrument_matching.matcher import match_instrument
from instrument_matching.repository import (
    WRITABLE_DECISIONS,
    fetch_pending_instruments,
    upsert_instrument_source,
)
from shared.config import YahooMatchSettings
from shared.db import connect_sql


def _match_pending_instruments(connection, client, settings):
    pending = fetch_pending_instruments(connection.cursor(), source="YAHOO")
    return [
        match_instrument(
            instrument,
            client,
            max_results=settings.max_results,
            automatic_threshold=settings.automatic_threshold,
            ambiguity_margin=settings.ambiguity_margin,
        )
        for instrument in pending
    ]


def _summary(results):
    counts = Counter(result["decision"] for result in results)
    return {
        "automatico": counts.get("AUTOMATICO", 0),
        "validado": counts.get("VALIDADO", 0),
        "excluido": counts.get("EXCLUIDO", 0),
        "revisar": counts.get("REVISAR", 0),
        "sinMatch": counts.get("SIN_MATCH", 0),
        "error": counts.get("ERROR", 0),
    }


def _create_yahoo_client(settings):
    return YahooSearchClient(
        settings.search_url,
        timeout_seconds=settings.request_timeout_seconds,
    )


def run_yahoo_matching_dry_run(settings=None, client=None):
    settings = settings or YahooMatchSettings.from_environment()
    owned_client = client is None
    if owned_client:
        client = _create_yahoo_client(settings)

    connection = None
    try:
        connection = connect_sql(settings.sql_connection_string)
        results = _match_pending_instruments(connection, client, settings)
        summary = _summary(results)
        status = "PARCIAL" if summary["error"] else "OK"
        return {
            "status": status,
            "mode": "DRY_RUN",
            "source": "YAHOO",
            "generatedAtUTC": datetime.now(timezone.utc).isoformat(),
            "writesPerformed": 0,
            "total": len(results),
            "summary": summary,
            "results": results,
        }
    finally:
        if connection is not None:
            connection.close()
        if owned_client:
            client.close()


def run_yahoo_matching_apply(settings=None, client=None):
    settings = settings or YahooMatchSettings.from_environment()
    owned_client = client is None
    if owned_client:
        client = _create_yahoo_client(settings)

    connection = None
    try:
        connection = connect_sql(settings.sql_connection_string)
        results = _match_pending_instruments(connection, client, settings)
        cursor = connection.cursor()
        written = 0
        for result in results:
            if result["decision"] not in WRITABLE_DECISIONS:
                result["writeApplied"] = False
                continue
            upsert_instrument_source(cursor, result, source="YAHOO")
            result["writeApplied"] = True
            written += 1

        connection.commit()
        summary = _summary(results)
        incomplete = summary["revisar"] + summary["sinMatch"] + summary["error"]
        return {
            "status": "PARCIAL" if incomplete else "OK",
            "mode": "APPLY",
            "source": "YAHOO",
            "generatedAtUTC": datetime.now(timezone.utc).isoformat(),
            "writesPerformed": written,
            "committed": True,
            "total": len(results),
            "summary": summary,
            "results": results,
        }
    except Exception:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                logging.exception("Falló el rollback del matching Yahoo.")
        raise
    finally:
        if connection is not None:
            connection.close()
        if owned_client:
            client.close()
