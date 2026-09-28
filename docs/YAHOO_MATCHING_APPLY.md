# Aplicación controlada del matching Yahoo

Implementada el 28 de septiembre de 2026. La Function reutiliza exactamente
las reglas auditadas por el `dry-run` y persiste solo decisiones
`AUTOMATICO` y `VALIDADO` mediante `dbo.sp_UpsertInstrumentoFuente`.

## Endpoint

```text
POST /api/instrumentos/matching/yahoo/apply
Autenticación: Function
Content-Type: application/json
```

El cuerpo debe confirmar explícitamente la operación:

```json
{
  "confirm": true
}
```

Un cuerpo ausente, inválido o sin el booleano exacto `true` responde `400` y
no ejecuta el servicio de escritura.

## Comportamiento

1. Lee pendientes mediante `dbo.sp_InstrumentosPendientesFuente`.
2. Ejecuta el mismo matching de Yahoo usado por el `dry-run`.
3. Llama a `dbo.sp_UpsertInstrumentoFuente` solo para resultados
   `AUTOMATICO` o `VALIDADO`.
4. Omite `EXCLUIDO`, `REVISAR`, `SIN_MATCH` y `ERROR`.
5. Confirma la transacción al terminar todos los upserts.
6. Ante una excepción, ejecuta `rollback`, cierra la conexión y devuelve un
   error sanitizado.

El procedimiento existente hace la operación idempotente por la combinación
`InstrumentoID`, `Fuente` y `SimboloFuente`. Una ejecución posterior actualiza
la relación conocida en lugar de duplicarla.

## Seguridad

La identidad administrada `func-bvc-mgc-cpabaas-dev` pertenece al rol
`instrument_enrichment_loader`, que tiene exclusivamente `EXECUTE` sobre:

- `dbo.sp_InstrumentosPendientesFuente`.
- `dbo.sp_UpsertInstrumentoFuente`.

No se concedieron roles amplios ni permisos directos adicionales sobre las
tablas de enriquecimiento.

## Estado operativo

El endpoint se despliega listo para su primera ejecución manual, pero el
despliegue no lo invoca. Antes de aplicar se debe revisar una vez más el
`dry-run`. El resultado esperado es escribir 10 relaciones y omitir PEI.

