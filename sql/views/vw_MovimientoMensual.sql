SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE   VIEW dbo.vw_MovimientoMensual
AS

SELECT
    O.OrdenID,
    O.PortafolioID,
    O.InstrumentoID,

    I.NombreInstrumento,
    I.TickerNegociacion,
    I.TickerSubyacente,

    CAST(O.FechaHoraOrdenUTC AS DATE) AS FechaOperacion,

    EOMONTH(O.FechaHoraOrdenUTC) AS FechaCorteMes,

    YEAR(O.FechaHoraOrdenUTC) AS Anio,
    MONTH(O.FechaHoraOrdenUTC) AS Mes,

    O.TipoOperacion,
    O.TipoOrden,

    O.CantidadSolicitada,

    O.CantidadEjecutadaAcumulada
        AS CantidadEjecutada,

    /* Cantidad con signo para analisis */
    CASE
        WHEN UPPER(LTRIM(RTRIM(O.TipoOperacion))) = 'COMPRA'
            THEN O.CantidadEjecutadaAcumulada

        WHEN UPPER(LTRIM(RTRIM(O.TipoOperacion))) = 'VENTA'
            THEN -O.CantidadEjecutadaAcumulada

        ELSE NULL
    END AS CantidadNeta,

    /*
       IMPORTANTE:
       Este es el precio inicial de la orden,
       no necesariamente el precio final de ejecucion.
    */
    O.PrecioInicialCOP
        AS PrecioReferenciaCOP,

    /*
       Valor indicativo.
       No debe tratarse como valor contable definitivo.
    */
    CASE
        WHEN O.PrecioInicialCOP IS NOT NULL
        THEN
            O.CantidadEjecutadaAcumulada
            * O.PrecioInicialCOP
        ELSE NULL
    END AS ValorReferenciaCOP,

    O.ComisionInicialCOP,

    O.MontoInicialCOP,

    O.Estado,

    O.CodigoOrdenBolsa,
    O.NumeroOrdenTrii,

    O.FechaCargaUTC,
    O.FechaActualizacionUTC

FROM dbo.Orden O

INNER JOIN dbo.Instrumento I
    ON I.InstrumentoID = O.InstrumentoID

/*
   Una orden puede terminar como NO_COMPLETADA
   después de haber tenido una ejecución parcial.

   Por eso filtramos por cantidad ejecutada,
   no por Estado.
*/
WHERE O.CantidadEjecutadaAcumulada > 0;
GO

