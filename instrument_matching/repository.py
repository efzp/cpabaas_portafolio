PENDING_INSTRUMENTS_PROCEDURE = "dbo.sp_InstrumentosPendientesFuente"
UPSERT_INSTRUMENT_SOURCE_PROCEDURE = "dbo.sp_UpsertInstrumentoFuente"
WRITABLE_DECISIONS = {"AUTOMATICO", "VALIDADO"}


def fetch_pending_instruments(cursor, source="YAHOO"):
    """Lee el contrato SQL del matching sin consultar tablas directamente."""
    cursor.execute(
        "EXEC dbo.sp_InstrumentosPendientesFuente @Fuente = ?;",
        source,
    )
    column_names = [column[0] for column in cursor.description]
    return [dict(zip(column_names, row)) for row in cursor.fetchall()]


def upsert_instrument_source(cursor, match, source="YAHOO"):
    """Persiste exclusivamente un match aceptado mediante el contrato SQL."""
    decision = match.get("decision")
    candidate = match.get("topCandidate") or {}
    symbol = candidate.get("symbol")
    if decision not in WRITABLE_DECISIONS:
        raise ValueError("Solo se pueden persistir matches aceptados.")
    if not symbol:
        raise ValueError("El match aceptado debe incluir un símbolo de proveedor.")

    cursor.execute(
        """
        EXEC dbo.sp_UpsertInstrumentoFuente
            @InstrumentoID = ?,
            @Fuente = ?,
            @SimboloFuente = ?,
            @NombreFuente = ?,
            @ExchangeFuente = ?,
            @MonedaFuente = ?,
            @TipoActivoFuente = ?,
            @EstadoMatch = ?,
            @ScoreMatch = ?;
        """,
        match.get("instrumentoId"),
        source,
        symbol,
        candidate.get("longName") or candidate.get("shortName"),
        candidate.get("exchangeDisplay") or candidate.get("exchange"),
        candidate.get("currency"),
        candidate.get("quoteType"),
        decision,
        candidate.get("score"),
    )
