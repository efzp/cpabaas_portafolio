# Línea base de Azure SQL

Definiciones recuperadas en modo de solo lectura el 28 de septiembre de 2026
desde `sqldb-inversiones-cpabaas`, en el servidor
`sql-inversiones-cpabaas-01.database.windows.net`.

## Alcance

- Cinco tablas usadas por el cargador BVC/MGC y el enriquecimiento financiero.
- Los cuatro procedimientos que forman el contrato de validación y matching.
- La vista mensual consumida por el reporte.
- El rol de mínimo privilegio usado por la Function actual.

Los scripts no contienen datos, credenciales, cadenas de conexión ni secretos.
Son una línea base del estado desplegado, no una migración que deba ejecutarse
sobre la base existente.

Las tablas `InstrumentoFuente` e `IndicadorEmpresaMensual` conservan relaciones
con `Instrumento` y `Empresa`, que ya existen en Azure SQL pero quedan fuera de
este alcance. Los procedimientos también dependen de otros objetos operativos
descritos en `docs/PROJECT_CONTEXT.md`.

## Orden para un entorno vacío

Si estos scripts se usan como referencia para construir migraciones futuras,
las dependencias externas deben existir primero. Dentro de este directorio, el
orden lógico es:

1. `tables/BvcMgcCarga.sql`.
2. `tables/BvcMgcValorStage.sql` y `tables/BvcMgcValor.sql`.
3. `tables/InstrumentoFuente.sql` e
   `tables/IndicadorEmpresaMensual.sql`, después de `Instrumento` y `Empresa`.
4. `views/` y `procedures/`, después de todas sus dependencias.
5. `security/bvc_mgc_loader.sql`.

