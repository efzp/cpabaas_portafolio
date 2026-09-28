import json
import logging

import azure.functions as func

from bvc_mgc.service import run_bvc_load
from instrument_matching.service import run_yahoo_matching_dry_run


app = func.FunctionApp()


@app.function_name(name="CargarBvcMgcMensual")
@app.timer_trigger(
    schedule="%TIMER_SCHEDULE%",
    arg_name="my_timer",
    run_on_startup=False,
    use_monitor=True,
)
def cargar_bvc_mgc_mensual(my_timer: func.TimerRequest) -> None:
    if my_timer.past_due:
        logging.warning("La ejecución mensual de la BVC se inició con retraso.")

    result = run_bvc_load()
    logging.info("Resultado de carga BVC MGC: %s", json.dumps(result, ensure_ascii=False))


@app.function_name(name="CargarBvcMgcManual")
@app.route(
    route="bvc-mgc/cargar",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def cargar_bvc_mgc_manual(req: func.HttpRequest) -> func.HttpResponse:
    try:
        result = run_bvc_load()
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as error:
        logging.exception("Falló la carga manual BVC MGC.")
        return func.HttpResponse(
            json.dumps({"status": "ERROR", "message": str(error)}, ensure_ascii=False),
            status_code=500,
            mimetype="application/json",
        )


@app.function_name(name="YahooMatchingDryRun")
@app.route(
    route="instrumentos/matching/yahoo/dry-run",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
def yahoo_matching_dry_run(req: func.HttpRequest) -> func.HttpResponse:
    try:
        result = run_yahoo_matching_dry_run()
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Falló el matching Yahoo en modo dry-run.")
        return func.HttpResponse(
            json.dumps(
                {
                    "status": "ERROR",
                    "mode": "DRY_RUN",
                    "message": "No fue posible ejecutar el matching de instrumentos.",
                },
                ensure_ascii=False,
            ),
            status_code=500,
            mimetype="application/json",
        )
