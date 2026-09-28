-- Línea base de permisos de enriquecimiento verificada el 28 de septiembre
-- de 2026. La identidad administrada debe existir como usuario externo.

IF DATABASE_PRINCIPAL_ID(N'instrument_enrichment_loader') IS NULL
    CREATE ROLE [instrument_enrichment_loader];
GO

IF DATABASE_PRINCIPAL_ID(N'func-bvc-mgc-cpabaas-dev') IS NULL
    THROW 51000, 'Falta crear el usuario externo func-bvc-mgc-cpabaas-dev.', 1;
GO

ALTER ROLE [instrument_enrichment_loader]
    ADD MEMBER [func-bvc-mgc-cpabaas-dev];
GO

GRANT EXECUTE ON OBJECT::[dbo].[sp_InstrumentosPendientesFuente]
    TO [instrument_enrichment_loader];
GRANT EXECUTE ON OBJECT::[dbo].[sp_UpsertInstrumentoFuente]
    TO [instrument_enrichment_loader];
GO
