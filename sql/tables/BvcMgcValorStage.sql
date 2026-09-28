SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE [dbo].[BvcMgcValorStage]
(
    [CargaID] [bigint] NOT NULL,
    [FilaOrigen] [int] NOT NULL,
    [Nemo] [nvarchar](50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Nombre] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Isin] [nvarchar](30) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Emisor] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [IdentificadorEmisor] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Descripcion] [nvarchar](MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [UrlRelacionInversionista] [nvarchar](1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [UrlRegulador] [nvarchar](1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [MercadoSubyacenteFuente] [nvarchar](150) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [TipoValorFuente] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Pais] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [Patrocinador] [nvarchar](300) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [NitPatrocinador] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [EsValida] [bit] CONSTRAINT [DF_BvcMgcValorStage_EsValida] DEFAULT ((0)) NOT NULL,
    [ErrorValidacion] [nvarchar](1000) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    CONSTRAINT [PK_BvcMgcValorStage] PRIMARY KEY CLUSTERED ([CargaID] ASC, [FilaOrigen] ASC)
);
GO

CREATE NONCLUSTERED INDEX [IX_BvcMgcValorStage_Nemo] ON [dbo].[BvcMgcValorStage] ([CargaID] ASC, [Nemo] ASC);
GO

ALTER TABLE [dbo].[BvcMgcValorStage] WITH CHECK ADD CONSTRAINT [FK_BvcMgcValorStage_Carga] FOREIGN KEY ([CargaID]) REFERENCES [dbo].[BvcMgcCarga] ([CargaID]);
ALTER TABLE [dbo].[BvcMgcValorStage] CHECK CONSTRAINT [FK_BvcMgcValorStage_Carga];
GO

