SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE [dbo].[BvcMgcValor]
(
    [BvcMgcValorID] [bigint] IDENTITY(1,1) NOT NULL,
    [Nemo] [nvarchar](50) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [Nombre] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [Isin] [nvarchar](30) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Emisor] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [IdentificadorEmisor] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Descripcion] [nvarchar](MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [UrlRelacionInversionista] [nvarchar](1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [UrlRegulador] [nvarchar](1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [MercadoSubyacenteFuente] [nvarchar](150) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [TipoValorFuente] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Pais] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Patrocinador] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [NitPatrocinador] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [MonedaOrigen] [char](3) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [BolsaPrincipal] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [FechaListadoMgc] [date] NULL,
    [PrimeraCargaID] [bigint] NOT NULL,
    [UltimaCargaID] [bigint] NOT NULL,
    [AusenciasConsecutivas] [smallint] CONSTRAINT [DF_BvcMgcValor_Ausencias] DEFAULT ((0)) NOT NULL,
    [Activo] [bit] CONSTRAINT [DF_BvcMgcValor_Activo] DEFAULT ((1)) NOT NULL,
    [FechaCreacionUTC] [datetime2](0) CONSTRAINT [DF_BvcMgcValor_FechaCreacion] DEFAULT (sysutcdatetime()) NOT NULL,
    [FechaActualizacionUTC] [datetime2](0) CONSTRAINT [DF_BvcMgcValor_FechaActualizacion] DEFAULT (sysutcdatetime()) NOT NULL,
    CONSTRAINT [PK_BvcMgcValor] PRIMARY KEY CLUSTERED ([BvcMgcValorID] ASC),
    CONSTRAINT [UQ_BvcMgcValor_Nemo] UNIQUE NONCLUSTERED ([Nemo] ASC)
);
GO

ALTER TABLE [dbo].[BvcMgcValor] WITH CHECK ADD CONSTRAINT [FK_BvcMgcValor_PrimeraCarga] FOREIGN KEY ([PrimeraCargaID]) REFERENCES [dbo].[BvcMgcCarga] ([CargaID]);
ALTER TABLE [dbo].[BvcMgcValor] CHECK CONSTRAINT [FK_BvcMgcValor_PrimeraCarga];
GO

ALTER TABLE [dbo].[BvcMgcValor] WITH CHECK ADD CONSTRAINT [FK_BvcMgcValor_UltimaCarga] FOREIGN KEY ([UltimaCargaID]) REFERENCES [dbo].[BvcMgcCarga] ([CargaID]);
ALTER TABLE [dbo].[BvcMgcValor] CHECK CONSTRAINT [FK_BvcMgcValor_UltimaCarga];
GO

