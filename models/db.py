"""Utilidades de conexion y consultas para SQL Server."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

import pyodbc
from flask import current_app


class DatabaseConnectionError(Exception):
    """Representa problemas al conectarse con SQL Server."""


class DatabaseQueryError(Exception):
    """Representa problemas al ejecutar sentencias SQL."""


def _get_candidate_servers() -> list[str]:
    """Devuelve una lista de servidores candidatos para la conexion."""
    configured_server = current_app.config.get("SQL_ACTIVE_SERVER") or current_app.config["SQL_SERVER"]
    known_servers = [configured_server, r"localhost\SQLEXPRESS", r".\SQLEXPRESS"]
    unique_servers = []

    for server in known_servers:
        if server and server not in unique_servers:
            unique_servers.append(server)

    return unique_servers


def _build_connection_string(server: str, database_name: str) -> str:
    """Construye la cadena de conexion segun el tipo de autenticacion elegido."""
    connection_parts = [
        f"DRIVER={{{current_app.config['SQL_DRIVER']}}}",
        f"SERVER={server}",
        f"DATABASE={database_name}",
        f"Encrypt={current_app.config['SQL_ENCRYPT']}",
        "TrustServerCertificate=yes",
    ]

    if current_app.config.get("SQL_USERNAME") and current_app.config.get("SQL_PASSWORD"):
        connection_parts.extend(
            [
                f"UID={current_app.config['SQL_USERNAME']}",
                f"PWD={current_app.config['SQL_PASSWORD']}",
            ]
        )
    else:
        connection_parts.append(
            f"Trusted_Connection={current_app.config['SQL_TRUSTED_CONNECTION']}"
        )

    return ";".join(connection_parts) + ";"


def get_connection(database_name: str | None = None, autocommit: bool = False):
    """Abre una conexion a SQL Server con servidores de respaldo."""
    db_name = database_name or current_app.config["SQL_DATABASE"]
    last_error = None

    for server in _get_candidate_servers():
        try:
            connection = pyodbc.connect(
                _build_connection_string(server, db_name),
                autocommit=autocommit,
                timeout=current_app.config["SQL_TIMEOUT"],
            )
            current_app.config["SQL_ACTIVE_SERVER"] = server
            return connection
        except pyodbc.Error as error:
            last_error = error

    raise DatabaseConnectionError(
        "No fue posible conectar con SQL Server. "
        f"Verifica la instancia configurada. Ultimo detalle: {last_error}"
    )


def _rows_to_dicts(cursor, rows):
    """Convierte filas de pyodbc en diccionarios simples."""
    columns = [column[0] for column in cursor.description or []]
    return [dict(zip(columns, row)) for row in rows]


def fetch_all(query: str, params: Sequence | None = None):
    """Ejecuta un SELECT y devuelve todas las filas encontradas."""
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params or [])
            rows = cursor.fetchall()
            return _rows_to_dicts(cursor, rows)
    except pyodbc.Error as error:
        raise DatabaseQueryError(f"No fue posible consultar la base de datos: {error}") from error


def fetch_one(query: str, params: Sequence | None = None):
    """Ejecuta un SELECT y devuelve solo la primera fila."""
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params or [])
            row = cursor.fetchone()
            return _rows_to_dicts(cursor, [row])[0] if row else None
    except pyodbc.Error as error:
        raise DatabaseQueryError(f"No fue posible consultar la base de datos: {error}") from error


def execute_non_query(query: str, params: Sequence | None = None):
    """Ejecuta INSERT, UPDATE o DELETE y devuelve las filas afectadas."""
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params or [])
            connection.commit()
            return cursor.rowcount
    except pyodbc.Error as error:
        raise DatabaseQueryError(f"No fue posible actualizar la base de datos: {error}") from error


def execute_scalar(query: str, params: Sequence | None = None):
    """Ejecuta una consulta y devuelve el primer valor de la primera fila."""
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, params or [])
            row = cursor.fetchone()
            connection.commit()
            return row[0] if row else None
    except pyodbc.Error as error:
        raise DatabaseQueryError(f"No fue posible ejecutar la consulta: {error}") from error


def _split_sql_batches(script_content: str):
    """Divide un script SQL Server en lotes usando la palabra GO."""
    return [
        batch.strip()
        for batch in re.split(r"^\s*GO\s*$", script_content, flags=re.MULTILINE | re.IGNORECASE)
        if batch.strip()
    ]


def initialize_database():
    """Crea la base de datos, aplica el schema y siembra informacion inicial."""
    schema_path = Path(current_app.config["SCHEMA_PATH"])
    database_name = current_app.config["SQL_DATABASE"]

    try:
        with get_connection("master", autocommit=True) as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"IF DB_ID(N'{database_name}') IS NULL CREATE DATABASE [{database_name}]"
            )
    except pyodbc.Error as error:
        raise DatabaseConnectionError(
            f"No fue posible crear o validar la base {database_name}: {error}"
        ) from error

    if not schema_path.exists():
        raise DatabaseQueryError(
            f"No se encontro el archivo de esquema requerido en {schema_path}."
        )

    schema_batches = _split_sql_batches(schema_path.read_text(encoding="utf-8"))

    try:
        with get_connection(database_name) as connection:
            cursor = connection.cursor()
            for batch in schema_batches:
                cursor.execute(batch)
            connection.commit()
    except pyodbc.Error as error:
        raise DatabaseQueryError(f"No fue posible aplicar el schema SQL: {error}") from error

    # Importa aqui para evitar ciclos entre los modelos y el modulo de conexion.
    from models.producto import seed_default_products
    from models.usuario import seed_default_users

    seed_default_users()
    seed_default_products()
