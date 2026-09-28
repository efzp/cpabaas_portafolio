# Instrucciones del proyecto

Antes de cambiar código o SQL, leer `docs/PROJECT_CONTEXT.md`.

- Azure SQL es la fuente de verdad. Inspeccionar la definición desplegada antes
  de modificar tablas, vistas o procedimientos.
- No recrear objetos que ya existen ni cambiar su contrato sin analizar sus
  consumidores de Power Automate.
- No modificar `Instrumento.TickerNegociacion` para adaptarlo a proveedores.
- Guardar símbolos de proveedores en `InstrumentoFuente`.
- Mantener separados los flujos operativos y el enriquecimiento externo.
- Usar Managed Identity y mínimo privilegio; no usar credenciales SQL ni roles
  amplios.
- No copiar al repositorio secretos ni contraseñas presentes en exportaciones.
- Implementar matching conservador y enviar ambigüedades a `REVISAR`.
- Añadir pruebas antes de desplegar cambios en la Function App existente.
- No desarrollar la fase de tesis de inversión antes de completar la fase de
  símbolos y fundamentales.
