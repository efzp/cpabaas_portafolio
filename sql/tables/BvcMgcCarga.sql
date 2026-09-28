SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE [dbo].[BvcMgcCarga]
(
    [CargaID] [bigint] IDENTITY(1,1) NOT NULL,
    [FuentePaginaUrl] [nvarchar](500) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [FuenteArchivoUrl] [nvarchar](1000) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [NombreArchivo] [nvarchar](260) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [ETag] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [UltimaModificacionFuente] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [HashSha256] [char](64) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [FechaInicioUTC] [datetime2](0) CONSTRAINT [DF_BvcMgcCarga_FechaInicio] DEFAULT (sysutcdatetime()) NOT NULL,
    [FechaFinUTC] [datetime2](0) NULL,
    [Estado] [varchar](30) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [TotalFilas] [int] NULL,
    [FilasValidas] [int] NULL,
    [FilasRechazadas] [int] NULL,
    [Mensaje] [nvarchar](2000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    CONSTRAINT [PK_BvcMgcCarga] PRIMARY KEY CLUSTERED ([CargaID] ASC)
);
GO

ALTER TABLE [dbo].[BvcMgcCarga] WITH CHECK ADD CONSTRAINT [CK_BvcMgcCarga_Estado] CHECK ([Estado]='ERROR' OR [Estado]='REQUIERE_REVISION' OR [Estado]='SIN_CAMBIOS' OR [Estado]='OK' OR [Estado]='PROCESANDO');
ALTER TABLE [dbo].[BvcMgcCarga] CHECK CONSTRAINT [CK_BvcMgcCarga_Estado];
GO

CREATE NONCLUSTERED INDEX [IX_BvcMgcCarga_Hash] ON [dbo].[BvcMgcCarga] ([HashSha256] ASC, [Estado] ASC);
GO

