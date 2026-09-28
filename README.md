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
[docs/DEPLOYED_BASELINE.md](docs/DEPLOYED_BASELINE.md), y la línea base de los
objetos críticos de Azure SQL se encuentra en [sql/README.md](sql/README.md).

> Importante: el cargador recuperado fue modularizado, probado y desplegado
> mediante GitHub Actions. No incorpora todavía enriquecimiento financiero.

## Estructura del código

```text
function_app.py        Disparadores de Azure Functions
bvc_mgc/parser.py      Lectura y validación del Excel
bvc_mgc/repository.py  Operaciones SQL del catálogo
bvc_mgc/service.py     Orquestación de la carga BVC/MGC
instrument_matching/   Matching Yahoo conservador y auditable
shared/config.py       Configuración desde variables de entorno
shared/db.py           Apertura de conexiones SQL
tests/                 Pruebas unitarias de caracterización
sql/                   Línea base de los objetos críticos de Azure SQL
.github/workflows/     Validación y despliegue mediante OIDC
```

La modularización conserva los nombres, rutas, programación y respuestas de
los disparadores recuperados del despliegue.

## Matching Yahoo dry-run

El endpoint `POST /api/instrumentos/matching/yahoo/dry-run` propone símbolos de
Yahoo sin escribir en SQL. Su diseño, criterios y primera ejecución están en
[docs/YAHOO_MATCHING_DRY_RUN.md](docs/YAHOO_MATCHING_DRY_RUN.md).

## Pruebas

```powershell
python -m compileall -q function_app.py shared bvc_mgc tests
python -m unittest discover -s tests -v
```
