SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE   PROCEDURE dbo.sp_ResolverInstrumentosExtracto
    @ExtractoID BIGINT
AS
BEGIN
    SET NOCOUNT ON;

    /* =====================================================
       1. Coincidencia exacta
       Ej: ECOPETROL -> ECOPETROL
           BRKB      -> BRKB
       ===================================================== */

    UPDATE L
    SET L.InstrumentoID = I.InstrumentoID
    FROM dbo.ExtractoPosicionLote L
    INNER JOIN dbo.Instrumento I
        ON UPPER(LTRIM(RTRIM(L.TickerExtracto)))
         = UPPER(LTRIM(RTRIM(I.TickerNegociacion)))
    WHERE L.ExtractoID = @ExtractoID
      AND L.InstrumentoID IS NULL
      AND I.Activo = 1;


    /* =====================================================
       2. Si no hubo coincidencia y termina en CO,
          probar el ticker sin los dos últimos caracteres.

          IMPORTANTE:
          solo se asigna si ese ticker raíz YA existe.
       ===================================================== */

    UPDATE L
    SET L.InstrumentoID = I.InstrumentoID
    FROM dbo.ExtractoPosicionLote L
    INNER JOIN dbo.Instrumento I
        ON UPPER(LTRIM(RTRIM(I.TickerNegociacion)))
         =
         UPPER(
            LEFT(
                LTRIM(RTRIM(L.TickerExtracto)),
                LEN(LTRIM(RTRIM(L.TickerExtracto))) - 2
            )
         )
    WHERE L.ExtractoID = @ExtractoID
      AND L.InstrumentoID IS NULL
      AND RIGHT(
            UPPER(LTRIM(RTRIM(L.TickerExtracto))),
            2
          ) = 'CO'
      AND LEN(LTRIM(RTRIM(L.TickerExtracto))) > 2
      AND I.Activo = 1;


    /* =====================================================
       3. Resultado
       ===================================================== */

    SELECT
        @ExtractoID AS ExtractoID,
        COUNT(*) AS TotalPosiciones,
        SUM(
            CASE
                WHEN InstrumentoID IS NULL THEN 1
                ELSE 0
            END
        ) AS SinInstrumentoID
    FROM dbo.ExtractoPosicionLote
    WHERE ExtractoID = @ExtractoID;
END;
GO

