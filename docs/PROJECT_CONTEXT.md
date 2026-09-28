# Contexto técnico del proyecto

Estado verificado el 28 de septiembre de 2026. Este documento resume el
handoff técnico, las exportaciones de Power Automate, el código desplegado en
Azure Functions y una inspección de solo lectura de Azure SQL.

## Objetivo

Generar un reporte mensual del portafolio de tesorería de CPABAAS que permita
conocer valor, composición, compras, ventas, rentabilidad, fundamentales y
estado de las tesis de inversión. No se pretende construir un back-office ni
una conciliación integral de broker.

## Arquitectura

```text
Correos Trii ──> Power Automate ──> Orden / OrdenEvento
                                            │
                                            ├──> vw_MovimientoMensual ──┐
Extracto PDF ─> Power Automate ──> ExtractoMensual                     │
                                  ExtractoPosicionLote                 │
                                            │                          │
                                            └──> CierreMensual         │
                                                 PosicionMensual ──────┤
                                                                       ├──> Power BI
Catálogo BVC/MGC ──> Azure Function ──> BvcMgc* ───────────────────────┤
                                                                       │
Fuentes financieras ─> Azure Function ─> InstrumentoFuente            │
                                           Empresa                     │
                                           IndicadorEmpresaMensual ────┘

DecisionInversion ─────────────────────────────────────────────────────> Power BI
```

Responsabilidades acordadas:

- Power Automate realiza orquestación e ingestión sencilla.
- Azure SQL es la fuente de verdad y contiene validación y consolidación.
- Azure Functions realiza integraciones externas y lógica Python.
- Power BI consume el modelo; no resuelve tickers ni contiene lógica compleja.

## Infraestructura verificada

- Grupo de recursos: `rg-inversiones-cpabaas`.
- Azure SQL: `sql-inversiones-cpabaas-01.database.windows.net`.
- Base: `sqldb-inversiones-cpabaas`.
- Function App: `func-bvc-mgc-cpabaas-dev`.
- Runtime: Python 3.11 sobre Flex Consumption.
- Identidad: System Assigned Managed Identity.
- Almacenamiento de despliegue y Document Intelligence también existen.
- Azure SQL es serverless, con pausa automática después de 60 minutos.

## Power Automate verificado

### TRII - Procesar ordenes

Lee correos con asunto asociado a Trii, convierte HTML a texto, clasifica el
mensaje y ejecuta `dbo.sp_ProcesarCorreoTrii`. Registra órdenes y eventos sin
sumar cantidades acumuladas: se conserva el máximo ejecutado reportado por
Trii.

Datos presentes:

- 36 órdenes: 29 completas y 7 no completadas.
- 63 eventos: 56 reportes de ejecución y 7 no completados.

`dbo.vw_MovimientoMensual` deriva compras y ventas desde las órdenes. El precio
es de referencia, no necesariamente el precio final ejecutado. No se debe
crear otra tabla Movimiento para duplicar este propósito.

### AV - Procesar extracto mensual

Recibe el PDF, valida origen, desbloquea el documento, usa Document
Intelligence, extrae resumen y lotes, resuelve instrumentos, valida el extracto
y genera el cierre mensual. El PDF final se conserva en OneDrive.

Datos presentes:

- 32 extractos `PROCESADO`, entre octubre de 2023 y agosto de 2026.
- 274 lotes; todos tienen `InstrumentoID` resuelto.
- 32 cierres `CERRADO`.
- 124 posiciones mensuales consolidadas.

Los 274 lotes conservan `EstadoConciliacion = PENDIENTE`. Debe definirse si ese
estado representa una tarea real pendiente o si debe actualizarse al completar
la validación.

## Azure Function verificada

La Function desplegada todavía no es el servicio de enriquecimiento. Es un
cargador del catálogo BVC/MGC con dos disparadores:

- `CargarBvcMgcManual`: HTTP POST con autenticación de nivel Function.
- `CargarBvcMgcMensual`: `0 0 11 1 * *`, primer día del mes a las 11:00 UTC.

El código descarga un XLSX, normaliza y valida sus filas, usa staging, controla
duplicados por SHA-256, detecta caídas superiores al 20 %, actualiza el catálogo
y desactiva valores después de dos ausencias consecutivas.

Estado de datos:

- Una carga `OK` con 134 valores válidos y cero rechazados.
- Una carga `SIN_CAMBIOS` del mismo archivo.
- 134 filas en `BvcMgcValor` y 134 en `BvcMgcValorStage`.

El despliegue activo fue publicado el 14 de septiembre de 2026. Su código
fuente fue recuperado e incorporado como línea base el 28 de septiembre de
2026. La procedencia y los hashes están en `DEPLOYED_BASELINE.md`.

La línea base fue modularizada el 28 de septiembre de 2026. Los disparadores
permanecen en `function_app.py`; parser, persistencia y servicio BVC/MGC están
en `bvc_mgc/`, y configuración/conexión en `shared/`. Trece pruebas unitarias
verifican el comportamiento principal. Esta versión fue desplegada con éxito
en Azure mediante GitHub Actions y OIDC. El workflow también quedó habilitado
para validar y desplegar cambios enviados a `main`.

## Modelo SQL y avance

Objetos ya creados que no deben recrearse:

- `dbo.InstrumentoFuente`.
- `dbo.IndicadorEmpresaMensual`.
- `dbo.sp_InstrumentosPendientesFuente`.
- `dbo.sp_UpsertInstrumentoFuente`.
- `dbo.sp_ResolverInstrumentosExtracto`.
- `dbo.sp_ValidarExtractoMensual` con validación y cierre integrados.
- `dbo.vw_MovimientoMensual`.

La validación integrada está desplegada y el backfill histórico está completo.

El 28 de septiembre de 2026 se recuperó en modo de solo lectura y se versionó
en `sql/` la definición desplegada de las cinco tablas críticas del cargador y
del enriquecimiento, los cuatro procedimientos del contrato de matching y
validación, `vw_MovimientoMensual` y el rol `bvc_mgc_loader`. Los scripts no
contienen datos ni credenciales y no fueron ejecutados contra Azure SQL.

Conteos relevantes:

| Objeto | Filas |
|---|---:|
| Empresa | 1 |
| Instrumento | 13 |
| InstrumentoAlias | 13 |
| InstrumentoFuente | 0 |
| IndicadorEmpresaMensual | 0 |
| Precio | 0 |
| Movimiento | 0 |
| DecisionInversion | 0 |

Esto ubica al proyecto después de la ingestión y consolidación, pero antes del
enriquecimiento financiero.

## Identidad y permisos

La Function usa identidad administrada y existe como usuario externo en SQL.
Actualmente pertenece al rol `bvc_mgc_loader`, limitado a `SELECT`, `INSERT` y
`UPDATE` sobre:

- `dbo.BvcMgcCarga`.
- `dbo.BvcMgcValorStage`.
- `dbo.BvcMgcValor`.

No tiene todavía `EXECUTE` sobre los procedimientos de enriquecimiento. No se
deben asignar `db_owner`, `db_datareader` ni `db_datawriter`.

## Decisiones y restricciones

- Preservar siempre `Instrumento.TickerNegociacion`.
- Guardar el símbolo exacto de cada proveedor en `InstrumentoFuente`.
- No hacer llamadas financieras dentro de los flujos operativos del PDF.
- No crear instrumentos arbitrariamente desde la Function.
- Usar procedimientos almacenados como contrato de lectura y escritura.
- El matching debe ser conservador; los casos ambiguos terminan en `REVISAR`.
- PEI y símbolos históricos como PFBCOLOM requieren tratamiento especial.
- Los fundamentales se cargan mensualmente solo para instrumentos presentes en
  el cierre.
- No desarrollar todavía `DecisionInversion`; primero deben completarse los
  fundamentales.

## Hallazgos de seguridad y operación

- La exportación del flujo de extractos contiene una contraseña de PDF en texto
  claro. No debe copiarse al repositorio; se debe rotar y mover a un secreto o
  parámetro protegido.
- El flujo Trii filtra el asunto, pero no muestra una validación explícita del
  remitente antes de escribir en SQL.
- El parsing depende de textos y posiciones del correo/PDF; requiere pruebas de
  regresión con ejemplos anonimizados.
- El endpoint manual devuelve mensajes de excepción internos y debe responder
  con un error sanitizado.
- Los paquetes exportados de Power Automate aún no tienen una línea base
  versionada y reproducible. El código Python y los objetos SQL críticos ya
  están versionados.

## Próximo objetivo técnico

El siguiente hito es una primera versión controlada del enriquecimiento de
instrumentos. Antes de desplegar funcionalidad nueva se debe establecer la
línea base del repositorio.

Orden recomendado:

1. ~~Recuperar del paquete desplegado `function_app.py`, `host.json` y
   `requirements.txt`, revisarlos y versionarlos sin secretos.~~ Completado
   el 28 de septiembre de 2026.
2. ~~Exportar a `sql/` las definiciones vigentes de las tablas, vista y
   procedimientos usados por el proyecto.~~ Completado el 28 de septiembre de
   2026 para los objetos críticos y los permisos del cargador.
3. ~~Separar acceso SQL, configuración y lógica del cargador BVC/MGC en
   módulos comprobables, conservando su comportamiento.~~ Completado el 28 de
   septiembre de 2026 con 13 pruebas unitarias y desplegado mediante GitHub
   Actions.
4. Implementar el servicio de matching Yahoo en modo `dry-run` usando
   `sp_InstrumentosPendientesFuente`.
5. Añadir pruebas para canonización, generación de candidatos, scoring,
   ambigüedad y casos PEI/PFBCOLOM.
6. Revisar manualmente los resultados del `dry-run` para los instrumentos
   actualmente presentes en `PosicionMensual`.
7. Crear un rol específico de enriquecimiento y conceder únicamente `EXECUTE`
   sobre `sp_InstrumentosPendientesFuente` y `sp_UpsertInstrumentoFuente`.
8. Habilitar la escritura mediante `sp_UpsertInstrumentoFuente` y desplegar un
   disparador diario independiente del cargador mensual BVC/MGC.
9. Solo después de estabilizar los símbolos, implementar los procedimientos y
   la carga mensual de fundamentales.

El primer entregable no es aún la descarga de fundamentales: es una Function
capaz de producir matches auditables y conservadores, primero sin escribir y
luego mediante el procedimiento almacenado autorizado.
