PENDING_INSTRUMENTS_PROCEDURE = "dbo.sp_InstrumentosPendientesFuente"


def fetch_pending_instruments(cursor, source="YAHOO"):
    """Lee el contrato SQL del matching sin consultar tablas directamente."""
    cursor.execute(
        "EXEC dbo.sp_InstrumentosPendientesFuente @Fuente = ?;",
        source,
    )
    column_names = [column[0] for column in cursor.description]
    return [dict(zip(column_names, row)) for row in cursor.fetchall()]

