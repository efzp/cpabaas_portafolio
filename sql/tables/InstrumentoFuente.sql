SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE [dbo].[InstrumentoFuente]
(
    [InstrumentoFuenteID] [bigint] IDENTITY(1,1) NOT NULL,
    [InstrumentoID] [int] NOT NULL,
    [Fuente] [nvarchar](30) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [SimboloFuente] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [NombreFuente] [nvarchar](400) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [ExchangeFuente] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [MonedaFuente] [char](3) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [TipoActivoFuente] [nvarchar](50) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [EstadoMatch] [nvarchar](20) COLLATE SQL_Latin1_General_CP1_CI_AS CONSTRAINT [DF_InstrumentoFuente_Estado] DEFAULT ('PENDIENTE') NOT NULL,
    [ScoreMatch] [decimal](6,5) NULL,
    [EsPrincipal] [bit] CONSTRAINT [DF_InstrumentoFuente_Principal] DEFAULT ((0)) NOT NULL,
    [FechaInicioVigencia] [date] NULL,
    [FechaFinVigencia] [date] NULL,
    [FechaUltimaValidacionUTC] [datetime2](7) CONSTRAINT [DF_InstrumentoFuente_Validacion] DEFAULT (sysutcdatetime()) NOT NULL,
    [FechaCreacionUTC] [datetime2](7) CONSTRAINT [DF_InstrumentoFuente_Creacion] DEFAULT (sysutcdatetime()) NOT NULL,
    CONSTRAINT [PK_InstrumentoFuente] PRIMARY KEY CLUSTERED ([InstrumentoFuenteID] ASC),
    CONSTRAINT [UQ_InstrumentoFuente_Simbolo] UNIQUE NONCLUSTERED ([InstrumentoID] ASC, [Fuente] ASC, [SimboloFuente] ASC)
);
GO

ALTER TABLE [dbo].[InstrumentoFuente] WITH CHECK ADD CONSTRAINT [CK_InstrumentoFuente_Estado] CHECK ([EstadoMatch]='DESCARTADO' OR [EstadoMatch]='REVISAR' OR [EstadoMatch]='VALIDADO' OR [EstadoMatch]='AUTOMATICO' OR [EstadoMatch]='PENDIENTE');
ALTER TABLE [dbo].[InstrumentoFuente] CHECK CONSTRAINT [CK_InstrumentoFuente_Estado];
GO

ALTER TABLE [dbo].[InstrumentoFuente] WITH CHECK ADD CONSTRAINT [FK_InstrumentoFuente_Instrumento] FOREIGN KEY ([InstrumentoID]) REFERENCES [dbo].[Instrumento] ([InstrumentoID]);
ALTER TABLE [dbo].[InstrumentoFuente] CHECK CONSTRAINT [FK_InstrumentoFuente_Instrumento];
GO

