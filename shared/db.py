def connect_sql(connection_string):
    """Abre la conexión usando la autenticación definida externamente."""
    import mssql_python

    return mssql_python.connect(connection_string)
