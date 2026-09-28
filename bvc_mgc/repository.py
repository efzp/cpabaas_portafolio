def insert_stage_rows(cursor, load_id, rows):
    statement = """
        INSERT INTO dbo.BvcMgcValorStage
        (
            CargaID, FilaOrigen, Nemo, Nombre, Isin, Emisor,
            IdentificadorEmisor, Descripcion, UrlRelacionInversionista,
            UrlRegulador, MercadoSubyacenteFuente, TipoValorFuente,
            Pais, Patrocinador, NitPatrocinador, EsValida, ErrorValidacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    parameters = [
        (
            load_id,
            row["row_number"],
            row["nemo"],
            row["name"],
            row["isin"],
            row["issuer"],
            row["issuer_id"],
            row["description"],
            row["investor_url"],
            row["regulator_url"],
            row["underlying_market_source"],
            row["security_type_source"],
            row["country"],
            row["sponsor"],
            row["sponsor_nit"],
            1 if row["is_valid"] else 0,
            row["validation_message"],
        )
        for row in rows
    ]
    cursor.executemany(statement, parameters)


def upsert_catalog(cursor, load_id, rows):
    cursor.execute(
        """
        UPDATE catalog
           SET AusenciasConsecutivas = AusenciasConsecutivas + 1,
               Activo = CASE
                   WHEN AusenciasConsecutivas + 1 >= 2 THEN 0
                   ELSE Activo
               END,
               FechaActualizacionUTC = SYSUTCDATETIME()
        FROM dbo.BvcMgcValor AS catalog
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM dbo.BvcMgcValorStage AS stage
            WHERE stage.CargaID = ?
              AND stage.EsValida = 1
              AND stage.Nemo = catalog.Nemo
        );
        """,
        load_id,
    )

    valid_rows = [row for row in rows if row["is_valid"]]
    for row in valid_rows:
        cursor.execute(
            "SELECT BvcMgcValorID FROM dbo.BvcMgcValor WHERE Nemo = ?;",
            row["nemo"],
        )
        existing = cursor.fetchone()

        common_parameters = (
            row["name"],
            row["isin"],
            row["issuer"],
            row["issuer_id"],
            row["description"],
            row["investor_url"],
            row["regulator_url"],
            row["underlying_market_source"],
            row["security_type_source"],
            row["country"],
            row["sponsor"],
            row["sponsor_nit"],
        )

        if existing:
            cursor.execute(
                """
                UPDATE dbo.BvcMgcValor
                   SET Nombre = ?,
                       Isin = ?,
                       Emisor = ?,
                       IdentificadorEmisor = ?,
                       Descripcion = ?,
                       UrlRelacionInversionista = ?,
                       UrlRegulador = ?,
                       MercadoSubyacenteFuente = ?,
                       TipoValorFuente = ?,
                       Pais = ?,
                       Patrocinador = ?,
                       NitPatrocinador = ?,
                       UltimaCargaID = ?,
                       AusenciasConsecutivas = 0,
                       Activo = 1,
                       FechaActualizacionUTC = SYSUTCDATETIME()
                 WHERE Nemo = ?;
                """,
                *common_parameters,
                load_id,
                row["nemo"],
            )
        else:
            cursor.execute(
                """
                INSERT INTO dbo.BvcMgcValor
                (
                    Nemo, Nombre, Isin, Emisor, IdentificadorEmisor,
                    Descripcion, UrlRelacionInversionista, UrlRegulador,
                    MercadoSubyacenteFuente, TipoValorFuente, Pais,
                    Patrocinador, NitPatrocinador, PrimeraCargaID,
                    UltimaCargaID, AusenciasConsecutivas, Activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1);
                """,
                row["nemo"],
                *common_parameters,
                load_id,
                load_id,
            )
