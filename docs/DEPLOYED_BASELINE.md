# Línea base desplegada de Azure Functions

Esta línea base fue recuperada el 28 de septiembre de 2026 desde el paquete
activo de `func-bvc-mgc-cpabaas-dev`. La recuperación fue de solo lectura y no
modificó el servicio desplegado.

## Origen

- Grupo de recursos: `rg-inversiones-cpabaas`.
- Function App: `func-bvc-mgc-cpabaas-dev`.
- Runtime: Python 3.11.
- Plan: Azure Functions Flex Consumption.
- Despliegue activo: `83872203-908c-40ed-be8f-3004534b9d0c`.
- Inicio del despliegue: `2026-09-14T15:04:21.0099649Z`.
- Fin exitoso: `2026-09-14T15:05:35.0357418Z`.

## Integridad

- Tamaño de `released-package.zip`: 21,397,869 bytes.
- SHA-256 del paquete:
  `f8731e0df2f6de6b565b919f4f17468a83755be825eb695a826e8078d1cbfaa2`.
- SHA-256 de `function_app.py` desplegado:
  `c9bf5f02058e8da59f3783f9be983e7e54b7c55a86e81348fb9b0aff6b57afe4`.
- SHA-256 de `host.json` desplegado:
  `fac28cd35d536a67ff49d191a09e12f7103e832bc8243f2b74efaeb63b806aa5`.
- SHA-256 de `requirements.txt` desplegado:
  `6004584b8d59b8d667d3ef772c10ce94fb424ac9a52bb070ea2b81ba381b2d41`.

Los archivos versionados se normalizaron a saltos de línea LF. También se
eliminaron espacios finales presentes en comentarios de `requirements.txt`.
Por esa razón, su hash en Git puede diferir del archivo empaquetado aunque el
contenido lógico sea equivalente.

## Archivos incorporados

- `function_app.py`.
- `host.json`.
- `requirements.txt`.
- `local.settings.example.json`, creado con marcadores sin secretos.

No se incorporaron dependencias empaquetadas, ZIP, manifiestos de Oryx, estado
de Kudu, cachés ni el archivo de respaldo encontrado en el paquete.

## Disparadores recuperados

- `CargarBvcMgcManual`: HTTP POST, autenticación de nivel Function y ruta
  `bvc-mgc/cargar`.
- `CargarBvcMgcMensual`: timer `%TIMER_SCHEDULE%`.
- Valor configurado en Azure al recuperar la línea base:
  `0 0 11 1 * *`.

## Configuración

El código obtiene la configuración exclusivamente desde variables de entorno:

- `AzureWebJobsStorage`.
- `BVC_MGC_PAGE_URL`.
- `BVC_MGC_FILE_URL`.
- `SQL_CONNECTION_STRING`.
- `TIMER_SCHEDULE`.

No se copiaron valores de Azure. La cadena SQL desplegada usa autenticación de
Microsoft Entra o identidad administrada.

## Verificaciones

- El despliegue activo figura como completo y exitoso.
- Se encontraron los dos disparadores esperados.
- El escaneo de los tres archivos no encontró contraseñas, claves de API,
  secretos ni cadenas de conexión embebidas.
- `function_app.py` superó la compilación sintáctica con `py_compile`.
- El contenido normalizado de los tres archivos coincide con el extraído del
  paquete desplegado.
- `host.json` y `local.settings.example.json` son JSON válidos.
- No se realizó despliegue, cambio de configuración ni escritura en Azure.
