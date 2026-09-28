SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE   PROCEDURE dbo.sp_InstrumentosPendientesFuente
    @Fuente NVARCHAR(30) = 'YAHOO'
AS
BEGIN

    SET NOCOUNT ON;

    SELECT DISTINCT
        I.InstrumentoID,
        I.EmpresaID,
        I.NombreInstrumento,
        I.TickerNegociacion,
        I.MercadoNegociacion,
        I.MonedaNegociacion,
        I.TickerSubyacente,
        I.MercadoOrigen,
        I.MonedaSubyacente,
        I.ISIN,

        E.NombreEmpresa

    FROM dbo.Instrumento I

    INNER JOIN dbo.PosicionMensual P
        ON P.InstrumentoID = I.InstrumentoID

    LEFT JOIN dbo.Empresa E
        ON E.EmpresaID = I.EmpresaID

    WHERE I.Activo = 1

      AND NOT EXISTS (
            SELECT 1
            FROM dbo.InstrumentoFuente F
            WHERE F.InstrumentoID = I.InstrumentoID
              AND F.Fuente = @Fuente
              AND F.EsPrincipal = 1
              AND F.EstadoMatch IN (
                    'AUTOMATICO',
                    'VALIDADO'
              )
      )

    ORDER BY I.InstrumentoID;

END;
GO

