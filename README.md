# CPABAAS Portafolio

Servicio serverless para el reporte mensual de inversiones de CPABAAS. Integra
Azure SQL con fuentes financieras externas para mantener el catálogo de
instrumentos, resolver símbolos de proveedores y cargar datos de mercado y
fundamentales.

El sistema completo se distribuye entre cuatro capas:

- Power Automate: ingestión de correos de Trii y extractos del broker.
- Azure SQL: modelo, integridad, validación y consolidación mensual.
- Azure Functions: catálogo BVC/MGC e integraciones financieras externas.
- Power BI: visualización y reporte mensual.

La arquitectura, el estado verificado y el plan inmediato están documentados
en [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md). La procedencia e
integridad del código recuperado están registradas en
[docs/DEPLOYED_BASELINE.md](docs/DEPLOYED_BASELINE.md).

> Importante: esta línea base reproduce el código recuperado del despliegue. No
> incorpora todavía modularización ni enriquecimiento financiero.
