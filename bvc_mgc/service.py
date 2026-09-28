import hashlib
import logging
import re

from bvc_mgc.parser import extract_mgc_rows
from bvc_mgc.repository import insert_stage_rows, upsert_catalog
from shared.config import BvcMgcSettings
from shared.db import connect_sql


def download_mgc_file(file_url, page_url):
    import requests

    return requests.get(
        file_url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; BVC-MGC-Loader/1.0)",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*",
            "Referer": page_url,
        },
        timeout=(20, 120),
    )


def get_filename(response):
    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', disposition)
    if match:
        return match.group(1).strip()
    return "Valores_listados_MGC.xlsx"


def run_bvc_load():
    settings = BvcMgcSettings.from_environment()
    page_url = settings.page_url
    file_url = settings.file_url

    response = download_mgc_file(file_url, page_url)
    response.raise_for_status()

    file_content = response.content
    if len(file_content) < 1000 or not file_content.startswith(b"PK"):
        raise ValueError("La respuesta recibida no parece ser un archivo XLSX válido.")

    file_hash = hashlib.sha256(file_content).hexdigest()
    filename = get_filename(response)
    etag = response.headers.get("ETag")
    last_modified = response.headers.get("Last-Modified")
    rows, sheet_name = extract_mgc_rows(file_content)

    total_rows = len(rows)
    valid_count = sum(1 for row in rows if row["is_valid"])
    rejected_count = total_rows - valid_count

    connection = None
    load_id = None

    try:
        connection = connect_sql(settings.sql_connection_string)
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT TOP (1) TotalFilas, FilasValidas, FilasRechazadas
            FROM dbo.BvcMgcCarga
            WHERE HashSha256 = ?
              AND Estado = 'OK'
            ORDER BY CargaID DESC;
            """,
            file_hash,
        )
        previous_same_file = cursor.fetchone()

        if previous_same_file:
            cursor.execute(
                """
                INSERT INTO dbo.BvcMgcCarga
                (
                    FuentePaginaUrl, FuenteArchivoUrl, NombreArchivo, ETag,
                    UltimaModificacionFuente, HashSha256, FechaFinUTC, Estado,
                    TotalFilas, FilasValidas, FilasRechazadas, Mensaje
                )
                VALUES (?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), 'SIN_CAMBIOS', ?, ?, ?, ?);
                """,
                page_url,
                file_url,
                filename,
                etag,
                last_modified,
                file_hash,
                previous_same_file[0],
                previous_same_file[1],
                previous_same_file[2],
                "El hash SHA-256 ya había sido procesado correctamente.",
            )
            connection.commit()
            return {
                "status": "SIN_CAMBIOS",
                "hash": file_hash,
                "file": filename,
            }

        cursor.execute(
            """
            INSERT INTO dbo.BvcMgcCarga
            (
                FuentePaginaUrl, FuenteArchivoUrl, NombreArchivo, ETag,
                UltimaModificacionFuente, HashSha256, Estado,
                TotalFilas, FilasValidas, FilasRechazadas, Mensaje
            )
            OUTPUT INSERTED.CargaID
            VALUES (?, ?, ?, ?, ?, ?, 'PROCESANDO', ?, ?, ?, ?);
            """,
            page_url,
            file_url,
            filename,
            etag,
            last_modified,
            file_hash,
            total_rows,
            valid_count,
            rejected_count,
            f"Hoja detectada: {sheet_name}",
        )
        load_id = cursor.fetchone()[0]
        connection.commit()

        insert_stage_rows(cursor, load_id, rows)

        cursor.execute(
            """
            SELECT TOP (1) FilasValidas
            FROM dbo.BvcMgcCarga
            WHERE Estado = 'OK'
              AND CargaID <> ?
            ORDER BY CargaID DESC;
            """,
            load_id,
        )
        previous_load = cursor.fetchone()
        previous_valid_count = previous_load[0] if previous_load else None

        requires_review = valid_count == 0 or (
            previous_valid_count
            and valid_count < previous_valid_count * 0.80
        )

        if requires_review:
            cursor.execute(
                """
                UPDATE dbo.BvcMgcCarga
                   SET Estado = 'REQUIERE_REVISION',
                       FechaFinUTC = SYSUTCDATETIME(),
                       Mensaje = ?
                 WHERE CargaID = ?;
                """,
                "La cantidad de filas válidas es cero o cayó más del 20%.",
                load_id,
            )
            connection.commit()
            return {
                "status": "REQUIERE_REVISION",
                "load_id": load_id,
                "total": total_rows,
                "valid": valid_count,
            }

        upsert_catalog(cursor, load_id, rows)

        cursor.execute(
            """
            UPDATE dbo.BvcMgcCarga
               SET Estado = 'OK',
                   FechaFinUTC = SYSUTCDATETIME(),
                   Mensaje = ?
             WHERE CargaID = ?;
            """,
            f"Carga completada desde la hoja {sheet_name}.",
            load_id,
        )
        connection.commit()

        return {
            "status": "OK",
            "load_id": load_id,
            "file": filename,
            "sheet": sheet_name,
            "total": total_rows,
            "valid": valid_count,
            "rejected": rejected_count,
        }

    except Exception as error:
        if connection is not None:
            try:
                connection.rollback()
                if load_id is not None:
                    cursor = connection.cursor()
                    cursor.execute(
                        """
                        UPDATE dbo.BvcMgcCarga
                           SET Estado = 'ERROR',
                               FechaFinUTC = SYSUTCDATETIME(),
                               Mensaje = ?
                         WHERE CargaID = ?;
                        """,
                        str(error)[:2000],
                        load_id,
                    )
                    connection.commit()
            except Exception:
                logging.exception("No fue posible registrar el error en Azure SQL.")
        raise
    finally:
        if connection is not None:
            connection.close()
