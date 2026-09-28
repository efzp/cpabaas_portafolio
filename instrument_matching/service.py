from collections import Counter
from datetime import datetime, timezone

from instrument_matching.client import YahooSearchClient
from instrument_matching.matcher import match_instrument
from instrument_matching.repository import fetch_pending_instruments
from shared.config import YahooMatchSettings
from shared.db import connect_sql


def run_yahoo_matching_dry_run(settings=None, client=None):
    settings = settings or YahooMatchSettings.from_environment()
    owned_client = client is None
    if owned_client:
        client = YahooSearchClient(
            settings.search_url,
            timeout_seconds=settings.request_timeout_seconds,
        )

    connection = None
    try:
        connection = connect_sql(settings.sql_connection_string)
        pending = fetch_pending_instruments(connection.cursor(), source="YAHOO")
        results = [
            match_instrument(
                instrument,
                client,
                max_results=settings.max_results,
                automatic_threshold=settings.automatic_threshold,
                ambiguity_margin=settings.ambiguity_margin,
            )
            for instrument in pending
        ]
        counts = Counter(result["decision"] for result in results)
        status = "PARCIAL" if counts.get("ERROR", 0) else "OK"
        return {
            "status": status,
            "mode": "DRY_RUN",
            "source": "YAHOO",
            "generatedAtUTC": datetime.now(timezone.utc).isoformat(),
            "writesPerformed": 0,
            "total": len(results),
            "summary": {
                "automatico": counts.get("AUTOMATICO", 0),
                "revisar": counts.get("REVISAR", 0),
                "sinMatch": counts.get("SIN_MATCH", 0),
                "error": counts.get("ERROR", 0),
            },
            "results": results,
        }
    finally:
        if connection is not None:
            connection.close()
        if owned_client:
            client.close()

