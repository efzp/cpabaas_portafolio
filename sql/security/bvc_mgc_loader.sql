-- Línea base de permisos desplegados. La identidad administrada debe crearse
-- como usuario externo antes de agregarla al rol en un entorno nuevo.

IF DATABASE_PRINCIPAL_ID(N'bvc_mgc_loader') IS NULL
    CREATE ROLE [bvc_mgc_loader];
GO

IF DATABASE_PRINCIPAL_ID(N'func-bvc-mgc-cpabaas-dev') IS NULL
    THROW 51000, 'Falta crear el usuario externo func-bvc-mgc-cpabaas-dev.', 1;
GO

ALTER ROLE [bvc_mgc_loader] ADD MEMBER [func-bvc-mgc-cpabaas-dev];
GO

GRANT SELECT, INSERT, UPDATE ON OBJECT::[dbo].[BvcMgcCarga]
    TO [bvc_mgc_loader];
GRANT SELECT, INSERT, UPDATE ON OBJECT::[dbo].[BvcMgcValorStage]
    TO [bvc_mgc_loader];
GRANT SELECT, INSERT, UPDATE ON OBJECT::[dbo].[BvcMgcValor]
    TO [bvc_mgc_loader];
GO

