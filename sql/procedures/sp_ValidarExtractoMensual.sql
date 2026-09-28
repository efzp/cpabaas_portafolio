SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE   PROCEDURE dbo.sp_ValidarExtractoMensual
    @ExtractoID BIGINT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE
        /* Extracto */
        @PortafolioID            INT,
        @FechaCorte              DATE,
        @RentaVariableCOP        DECIMAL(19,4),
        @EfectivoCOP             DECIMAL(19,4),
        @FondosCOP               DECIMAL(19,4),
        @PasivosCOP              DECIMAL(19,4),
        @TotalPortafolioCOP      DECIMAL(19,4),

        /* Validacion */
        @ValorMercadoLotes       DECIMAL(19,4),
        @TotalCalculado          DECIMAL(19,4),
        @DiferenciaRV            DECIMAL(19,4),
        @DiferenciaTotal         DECIMAL(19,4),

        @CantidadLotes           INT,
        @LineasDistintas         INT,
        @MinLinea                INT,
        @MaxLinea                INT,
        @FilasInvalidas          INT,
        @SinInstrumentoID        INT,

        @LineasOK                BIT,
        @Estado                  NVARCHAR(20),
        @Tolerancia              DECIMAL(19,4) = 1.00,

        /* Cierre */
        @CierreID                INT,
        @CantidadPosiciones      INT;

    BEGIN TRY

        BEGIN TRANSACTION;

        /* =====================================================
           1. Verificar existencia del extracto
           ===================================================== */

        IF NOT EXISTS (
            SELECT 1
            FROM dbo.ExtractoMensual
            WHERE ExtractoID = @ExtractoID
        )
        BEGIN
            THROW 51030,
                  'No se encontro el ExtractoID indicado.',
                  1;
        END;


        /* =====================================================
           2. Obtener datos del extracto
           ===================================================== */

        SELECT
            @PortafolioID        = PortafolioID,
            @FechaCorte          = FechaCorte,
            @RentaVariableCOP    = ISNULL(RentaVariableCOP, 0),
            @EfectivoCOP         = ISNULL(EfectivoCOP, 0),
            @FondosCOP           = ISNULL(FondosCOP, 0),
            @PasivosCOP          = ISNULL(PasivosCOP, 0),
            @TotalPortafolioCOP  = ISNULL(TotalPortafolioCOP, 0)
        FROM dbo.ExtractoMensual
        WHERE ExtractoID = @ExtractoID;


        /* =====================================================
           3. Analizar lotes del extracto
           ===================================================== */

        SELECT
            @CantidadLotes =
                COUNT(*),

            @LineasDistintas =
                COUNT(DISTINCT NumeroLinea),

            @MinLinea =
                MIN(NumeroLinea),

            @MaxLinea =
                MAX(NumeroLinea),

            @ValorMercadoLotes =
                ISNULL(SUM(ValorMercadoCOP), 0),

            @FilasInvalidas =
                ISNULL(
                    SUM(
                        CASE
                            WHEN NULLIF(
                                    LTRIM(RTRIM(TickerExtracto)),
                                    ''
                                 ) IS NULL
                              OR InstrumentoID IS NULL
                              OR Cantidad IS NULL
                              OR PrecioCompraCOP IS NULL
                              OR PrecioValoracionCOP IS NULL
                              OR ValorMercadoCOP IS NULL
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ),

            @SinInstrumentoID =
                ISNULL(
                    SUM(
                        CASE
                            WHEN InstrumentoID IS NULL
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                )

        FROM dbo.ExtractoPosicionLote
        WHERE ExtractoID = @ExtractoID;


        /* =====================================================
           4. Validar continuidad de NumeroLinea
           ===================================================== */

        SET @LineasOK =
            CASE

                /* Puede existir un extracto sin renta variable */
                WHEN @RentaVariableCOP = 0
                 AND @CantidadLotes = 0
                THEN 1

                /* Si hay lotes: 1...N sin huecos */
                WHEN @CantidadLotes > 0
                 AND @MinLinea = 1
                 AND @MaxLinea = @CantidadLotes
                 AND @LineasDistintas = @CantidadLotes
                THEN 1

                ELSE 0
            END;


        /* =====================================================
           5. Validar total de renta variable
           ===================================================== */

        SET @DiferenciaRV =
            @RentaVariableCOP
            - ISNULL(@ValorMercadoLotes, 0);


        /* =====================================================
           6. Validar total del portafolio
           ===================================================== */

        SET @TotalCalculado =
              ISNULL(@EfectivoCOP, 0)
            + ISNULL(@RentaVariableCOP, 0)
            + ISNULL(@FondosCOP, 0)
            - ISNULL(@PasivosCOP, 0);


        SET @DiferenciaTotal =
            @TotalPortafolioCOP
            - @TotalCalculado;


        /* =====================================================
           7. Resultado general de validacion
           ===================================================== */

        SET @Estado =
            CASE
                WHEN ABS(@DiferenciaRV) <= @Tolerancia
                 AND ABS(@DiferenciaTotal) <= @Tolerancia
                 AND @FilasInvalidas = 0
                 AND @SinInstrumentoID = 0
                 AND @LineasOK = 1
                THEN 'PROCESADO'

                ELSE 'REVISAR'
            END;


        /* =====================================================
           8. Actualizar estado del extracto
           ===================================================== */

        UPDATE dbo.ExtractoMensual
        SET
            EstadoProcesamiento = @Estado,

            Observaciones = CONCAT(
                'Validacion automatica | ',
                'Lotes: ',
                @CantidadLotes,

                ' | Valor mercado lotes: ',
                CONVERT(VARCHAR(50), @ValorMercadoLotes),

                ' | Diferencia RV: ',
                CONVERT(VARCHAR(50), @DiferenciaRV),

                ' | Diferencia total: ',
                CONVERT(VARCHAR(50), @DiferenciaTotal),

                ' | Filas invalidas: ',
                @FilasInvalidas,

                ' | Sin InstrumentoID: ',
                @SinInstrumentoID,

                ' | Lineas OK: ',
                CASE
                    WHEN @LineasOK = 1 THEN 'SI'
                    ELSE 'NO'
                END
            ),

            FechaProcesamientoUTC = SYSUTCDATETIME()

        WHERE ExtractoID = @ExtractoID;


        /* =====================================================
           9. Si falla validacion:
              no generar cierre
           ===================================================== */

        IF @Estado <> 'PROCESADO'
        BEGIN

            COMMIT TRANSACTION;

            SELECT
                @ExtractoID AS ExtractoID,
                @Estado AS EstadoProcesamiento,

                CAST(NULL AS INT) AS CierreID,
                0 AS CantidadPosiciones,

                @CantidadLotes AS CantidadLotes,
                @MinLinea AS MinLinea,
                @MaxLinea AS MaxLinea,
                @LineasDistintas AS LineasDistintas,
                @LineasOK AS LineasOK,

                @FilasInvalidas AS FilasInvalidas,
                @SinInstrumentoID AS SinInstrumentoID,

                @RentaVariableCOP AS RentaVariableExtracto,
                @ValorMercadoLotes AS ValorMercadoLotes,
                @DiferenciaRV AS DiferenciaRentaVariable,

                @TotalPortafolioCOP AS TotalPortafolioExtracto,
                @TotalCalculado AS TotalPortafolioCalculado,
                @DiferenciaTotal AS DiferenciaTotal;

            RETURN;
        END;


        /* =====================================================
           10. Validar moneda

           PosicionMensual se genera actualmente bajo COP.
           MGC sigue siendo negociacion en COP aunque el
           subyacente sea USD.
           ===================================================== */

        IF EXISTS (
            SELECT 1
            FROM dbo.ExtractoPosicionLote L
            INNER JOIN dbo.Instrumento I
                ON I.InstrumentoID = L.InstrumentoID
            WHERE L.ExtractoID = @ExtractoID
              AND I.MonedaNegociacion <> 'COP'
        )
        BEGIN
            THROW 51031,
                  'Hay instrumentos cuya moneda de negociacion no es COP.',
                  1;
        END;


        /* =====================================================
           11. Buscar cierre existente

           Solo puede existir uno por:
           PortafolioID + FechaCorte
           ===================================================== */

        SELECT
            @CierreID = CierreID
        FROM dbo.CierreMensual WITH (UPDLOCK, HOLDLOCK)
        WHERE PortafolioID = @PortafolioID
          AND FechaCorte = @FechaCorte;


        /* =====================================================
           12. Crear CierreMensual si no existe
           ===================================================== */

        IF @CierreID IS NULL
        BEGIN

            INSERT INTO dbo.CierreMensual
            (
                PortafolioID,
                FechaCorte,
                Estado,
                ResponsableCierre,
                Aprobador,
                FechaCierreUTC,
                Observaciones,
                ExtractoID
            )
            VALUES
            (
                @PortafolioID,
                @FechaCorte,
                'REVISION',
                'Proceso automatico',
                NULL,
                NULL,
                'Cierre mensual generado automaticamente.',
                @ExtractoID
            );

            SET @CierreID =
                CONVERT(INT, SCOPE_IDENTITY());

        END
        ELSE
        BEGIN

            /* =================================================
               Si el cierre ya existe, reutilizarlo.
               Esto permite reprocesar el mes.
               ================================================= */

            UPDATE dbo.CierreMensual
            SET
                ExtractoID = @ExtractoID,
                Estado = 'REVISION',
                FechaCierreUTC = NULL,
                Observaciones =
                    'Cierre mensual recalculado automaticamente.'
            WHERE CierreID = @CierreID;

        END;


        /* =====================================================
           13. Eliminar posiciones anteriores

           Permite recalcular el mismo cierre sin duplicados.
           ===================================================== */

        DELETE
        FROM dbo.PosicionMensual
        WHERE CierreID = @CierreID;


        /* =====================================================
           14. Generar PosicionMensual

           Una fila por:
           CierreID + InstrumentoID

           Los distintos lotes quedan consolidados.
           ===================================================== */

        INSERT INTO dbo.PosicionMensual
        (
            CierreID,
            InstrumentoID,
            Cantidad,
            CostoTotalMoneda,
            Moneda,
            PrecioCierre,
            ValorMercadoMoneda,
            TRMCierre,
            CostoTotalCOP,
            ValorMercadoCOP,
            GananciaNoRealizadaCOP,
            Rentabilidad,
            PesoPortafolio
        )

        SELECT
            @CierreID,

            L.InstrumentoID,


            /* Cantidad total */
            SUM(L.Cantidad),


            /* Costo en moneda de negociacion.
               Actualmente COP */
            SUM(L.CostoHistoricoCOP),


            I.MonedaNegociacion,


            /* Precio de cierre consolidado */
            CAST(
                CASE
                    WHEN SUM(L.Cantidad) <> 0
                    THEN
                        SUM(L.ValorMercadoCOP)
                        / SUM(L.Cantidad)
                    ELSE 0
                END
                AS DECIMAL(20,8)
            ),


            /* Valor mercado moneda */
            SUM(L.ValorMercadoCOP),


            /* No aplica TRM mientras negociacion sea COP */
            NULL,


            /* Costo total COP */
            SUM(L.CostoHistoricoCOP),


            /* Valor mercado COP */
            SUM(L.ValorMercadoCOP),


            /* Ganancia no realizada */
            SUM(L.ValorMercadoCOP)
                - SUM(L.CostoHistoricoCOP),


            /* Rentabilidad */
            CASE
                WHEN SUM(L.CostoHistoricoCOP) <> 0
                THEN
                    (
                        SUM(L.ValorMercadoCOP)
                        - SUM(L.CostoHistoricoCOP)
                    )
                    / SUM(L.CostoHistoricoCOP)

                ELSE NULL
            END,


            /* Peso sobre el portafolio total */
            CASE
                WHEN @TotalPortafolioCOP <> 0
                THEN
                    SUM(L.ValorMercadoCOP)
                    / @TotalPortafolioCOP

                ELSE NULL
            END

        FROM dbo.ExtractoPosicionLote L

        INNER JOIN dbo.Instrumento I
            ON I.InstrumentoID = L.InstrumentoID

        WHERE L.ExtractoID = @ExtractoID

        GROUP BY
            L.InstrumentoID,
            I.MonedaNegociacion;


        /* =====================================================
           15. Contar posiciones creadas
           ===================================================== */

        SELECT
            @CantidadPosiciones = COUNT(*)
        FROM dbo.PosicionMensual
        WHERE CierreID = @CierreID;


        /* =====================================================
           16. Cerrar el cierre mensual
           ===================================================== */

        UPDATE dbo.CierreMensual
        SET
            Estado = 'CERRADO',

            FechaCierreUTC =
                SYSUTCDATETIME(),

            ExtractoID =
                @ExtractoID,

            Observaciones =
                CONCAT(
                    'Cierre generado automaticamente | ',
                    'ExtractoID: ',
                    @ExtractoID,
                    ' | Posiciones: ',
                    @CantidadPosiciones
                )

        WHERE CierreID = @CierreID;


        /* =====================================================
           17. Confirmar transaccion
           ===================================================== */

        COMMIT TRANSACTION;


        /* =====================================================
           18. Resultado final para Power Automate
           ===================================================== */

        SELECT
            @ExtractoID AS ExtractoID,

            @Estado AS EstadoProcesamiento,

            @CierreID AS CierreID,

            @PortafolioID AS PortafolioID,

            @FechaCorte AS FechaCorte,

            'CERRADO' AS EstadoCierre,

            @CantidadPosiciones AS CantidadPosiciones,

            @CantidadLotes AS CantidadLotes,

            @MinLinea AS MinLinea,

            @MaxLinea AS MaxLinea,

            @LineasDistintas AS LineasDistintas,

            @LineasOK AS LineasOK,

            @FilasInvalidas AS FilasInvalidas,

            @SinInstrumentoID AS SinInstrumentoID,

            @RentaVariableCOP AS RentaVariableExtracto,

            @ValorMercadoLotes AS ValorMercadoLotes,

            @DiferenciaRV AS DiferenciaRentaVariable,

            @TotalPortafolioCOP AS TotalPortafolioExtracto,

            @TotalCalculado AS TotalPortafolioCalculado,

            @DiferenciaTotal AS DiferenciaTotal;

    END TRY
    BEGIN CATCH

        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;

    END CATCH;

END;
GO

