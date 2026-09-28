SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE [dbo].[IndicadorEmpresaMensual]
(
    [IndicadorEmpresaMensualID] [bigint] IDENTITY(1,1) NOT NULL,
    [FechaCorte] [date] NOT NULL,
    [InstrumentoID] [int] NOT NULL,
    [EmpresaID] [int] NULL,
    [Fuente] [nvarchar](30) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [SimboloFuente] [nvarchar](100) COLLATE SQL_Latin1_General_CP1_CI_AS NOT NULL,
    [Moneda] [char](3) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    [PrecioMercado] [decimal](28,8) NULL,
    [CapitalizacionMercado] [decimal](28,4) NULL,
    [EnterpriseValue] [decimal](28,4) NULL,
    [PER] [decimal](18,6) NULL,
    [EV_EBITDA] [decimal](18,6) NULL,
    [ROE] [decimal](18,8) NULL,
    [IngresosTTM] [decimal](28,4) NULL,
    [UtilidadNetaTTM] [decimal](28,4) NULL,
    [FlujoCajaLibreTTM] [decimal](28,4) NULL,
    [DeudaNeta] [decimal](28,4) NULL,
    [DividendYield] [decimal](18,8) NULL,
    [FechaFundamentales] [date] NULL,
    [FechaConsultaUTC] [datetime2](7) CONSTRAINT [DF_IndicadorEmpresaMensual_Fecha] DEFAULT (sysutcdatetime()) NOT NULL,
    [RawJson] [nvarchar](MAX) COLLATE SQL_Latin1_General_CP1_CI_AS NULL,
    CONSTRAINT [PK_IndicadorEmpresaMensual] PRIMARY KEY CLUSTERED ([IndicadorEmpresaMensualID] ASC),
    CONSTRAINT [UQ_IndicadorEmpresaMensual] UNIQUE NONCLUSTERED ([FechaCorte] ASC, [InstrumentoID] ASC, [Fuente] ASC)
);
GO

ALTER TABLE [dbo].[IndicadorEmpresaMensual] WITH CHECK ADD CONSTRAINT [FK_IndicadorEmpresaMensual_Empresa] FOREIGN KEY ([EmpresaID]) REFERENCES [dbo].[Empresa] ([EmpresaID]);
ALTER TABLE [dbo].[IndicadorEmpresaMensual] CHECK CONSTRAINT [FK_IndicadorEmpresaMensual_Empresa];
GO

ALTER TABLE [dbo].[IndicadorEmpresaMensual] WITH CHECK ADD CONSTRAINT [FK_IndicadorEmpresaMensual_Instrumento] FOREIGN KEY ([InstrumentoID]) REFERENCES [dbo].[Instrumento] ([InstrumentoID]);
ALTER TABLE [dbo].[IndicadorEmpresaMensual] CHECK CONSTRAINT [FK_IndicadorEmpresaMensual_Instrumento];
GO

