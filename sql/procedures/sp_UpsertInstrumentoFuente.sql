SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE   PROCEDURE dbo.sp_UpsertInstrumentoFuente
    @InstrumentoID INT,
    @Fuente NVARCHAR(30),
    @SimboloFuente NVARCHAR(100),
    @NombreFuente NVARCHAR(400) = NULL,
    @ExchangeFuente NVARCHAR(100) = NULL,
    @MonedaFuente CHAR(3) = NULL,
    @TipoActivoFuente NVARCHAR(50) = NULL,
    @EstadoMatch NVARCHAR(20),
    @ScoreMatch DECIMAL(6,5) = NULL
AS
BEGIN

    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @EsPrincipal BIT =
            CASE
                WHEN @EstadoMatch IN ('AUTOMATICO','VALIDADO')
                    THEN 1
                ELSE 0
            END;


        /* Si el nuevo match es aceptado,
           quitar principal anterior */
        IF @EsPrincipal = 1
        BEGIN

            UPDATE dbo.InstrumentoFuente
            SET
                EsPrincipal = 0,
                FechaFinVigencia =
                    ISNULL(FechaFinVigencia, CAST(GETDATE() AS DATE))
            WHERE InstrumentoID = @InstrumentoID
              AND Fuente = @Fuente
              AND EsPrincipal = 1;

        END;


        /* Actualizar si ya conocemos exactamente el símbolo */
        IF EXISTS (
            SELECT 1
            FROM dbo.InstrumentoFuente
            WHERE InstrumentoID = @InstrumentoID
              AND Fuente = @Fuente
              AND SimboloFuente = @SimboloFuente
        )
        BEGIN

            UPDATE dbo.InstrumentoFuente
            SET
                NombreFuente = @NombreFuente,
                ExchangeFuente = @ExchangeFuente,
                MonedaFuente = @MonedaFuente,
                TipoActivoFuente = @TipoActivoFuente,
                EstadoMatch = @EstadoMatch,
                ScoreMatch = @ScoreMatch,
                EsPrincipal = @EsPrincipal,
                FechaInicioVigencia =
                    CASE
                        WHEN @EsPrincipal = 1
                        THEN ISNULL(
                            FechaInicioVigencia,
                            CAST(GETDATE() AS DATE)
                        )
                        ELSE FechaInicioVigencia
                    END,
                FechaFinVigencia =
                    CASE
                        WHEN @EsPrincipal = 1
                        THEN NULL
                        ELSE FechaFinVigencia
                    END,
                FechaUltimaValidacionUTC =
                    SYSUTCDATETIME()

            WHERE InstrumentoID = @InstrumentoID
              AND Fuente = @Fuente
              AND SimboloFuente = @SimboloFuente;

        END
        ELSE
        BEGIN

            INSERT INTO dbo.InstrumentoFuente
            (
                InstrumentoID,
                Fuente,
                SimboloFuente,
                NombreFuente,
                ExchangeFuente,
                MonedaFuente,
                TipoActivoFuente,
                EstadoMatch,
                ScoreMatch,
                EsPrincipal,
                FechaInicioVigencia
            )
            VALUES
            (
                @InstrumentoID,
                @Fuente,
                @SimboloFuente,
                @NombreFuente,
                @ExchangeFuente,
                @MonedaFuente,
                @TipoActivoFuente,
                @EstadoMatch,
                @ScoreMatch,
                @EsPrincipal,
                CASE
                    WHEN @EsPrincipal = 1
                    THEN CAST(GETDATE() AS DATE)
                    ELSE NULL
                END
            );

        END;

        COMMIT TRANSACTION;

    END TRY
    BEGIN CATCH

        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;

    END CATCH;

END;
GO

