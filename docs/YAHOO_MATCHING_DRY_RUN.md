# Matching Yahoo en modo dry-run

Implementado y verificado el 28 de septiembre de 2026. El servicio consulta
`dbo.sp_InstrumentosPendientesFuente`, busca candidatos en Yahoo y devuelve
evidencia auditable. No ejecuta `dbo.sp_UpsertInstrumentoFuente`, no llama a
`commit` y reporta `writesPerformed = 0`.

## Endpoint

```text
POST /api/instrumentos/matching/yahoo/dry-run
Autenticación: Function
```

La respuesta contiene el resumen de decisiones, las consultas realizadas, el
mejor candidato, hasta cinco candidatos puntuados y el desglose de evidencia.
Los errores externos se informan por tipo sin exponer mensajes internos.

## Criterios conservadores

- Coincidencia con `TickerSubyacente`: hasta 0.60.
- Coincidencia exacta con símbolo BVC: hasta 0.50.
- Similitud de nombre: hasta 0.25.
- Mercado compatible: hasta 0.10.
- Tipo de activo: hasta 0.05.
- Umbral automático: 0.85.
- Margen mínimo frente al segundo candidato: 0.15.
- También se exige evidencia fuerte de identidad; un ticker aislado no basta.
- `PEI`, `PFBCOLOM` y `PFCIBEST` siempre terminan en `REVISAR`.

## Resultado inicial

La ejecución inicial usó los 11 instrumentos devueltos por el procedimiento y
realizó únicamente consultas de lectura a SQL y Yahoo.

| ID | Ticker | Mejor candidato | Score | Margen | Decisión |
|---:|---|---|---:|---:|---|
| 2 | BRKB | BRK-B | 1.00 | 0.60 | AUTOMATICO |
| 24 | ECOPETROL | ECOPETROL.CL | 0.65 | 0.60 | REVISAR |
| 25 | GEB | GEB.CL | 0.65 | 0.60 | REVISAR |
| 26 | CORFICOLCF | CORFICOLCF.CL | 0.65 | 0.65 | REVISAR |
| 28 | PEI | PEI.CL | 0.65 | 0.60 | REVISAR |
| 30 | MSFTCO | MSFTCO.CL | 0.65 | 0.30 | REVISAR |
| 39 | PFCIBEST | PFCIBEST.CL | 0.65 | 0.40 | REVISAR |
| 40 | ISA | ISA.CL | 0.65 | 0.60 | REVISAR |
| 42 | GOOGL | GOOGL | 0.50 | 0.45 | REVISAR |
| 44 | TERPEL | TERPEL.CL | 0.65 | 0.65 | REVISAR |
| 46 | PFBCOLOM | CIB | 0.25 | 0.20 | REVISAR |

No hubo errores del proveedor. Los diez resultados `REVISAR` requieren
validación de negocio antes de cualquier escritura. En particular, debe
confirmarse la relación histórica entre `PFBCOLOM`, `PFCIBEST` y `CIB`.

## Permiso pendiente

La identidad administrada de la Function aún no tiene `EXECUTE` sobre
`dbo.sp_InstrumentosPendientesFuente`. El endpoint puede desplegarse y las
pruebas pueden ejecutarse, pero no funcionará en Azure hasta crear el rol de
enriquecimiento de mínimo privilegio previsto en el siguiente paso.

