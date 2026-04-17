"""Configuracion central de PURA TENIS."""

import os
from pathlib import Path


# Calcula la raiz del proyecto para reutilizar rutas locales.
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Agrupa la configuracion de Flask y SQL Server."""

    # Define la clave secreta para sesiones y mensajes flash.
    SECRET_KEY = os.getenv("SECRET_KEY", "pura-tenis-secret-key")

    # Permite personalizar la conexion a SQL Server por variables de entorno.
    SQL_SERVER = os.getenv("SQL_SERVER", r"localhost\SQLEXPRESS")
    SQL_DATABASE = os.getenv("SQL_DATABASE", "PuraTenisDB")
    SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
    SQL_USERNAME = os.getenv("SQL_USERNAME", "")
    SQL_PASSWORD = os.getenv("SQL_PASSWORD", "")
    SQL_TRUSTED_CONNECTION = os.getenv("SQL_TRUSTED_CONNECTION", "yes")
    SQL_ENCRYPT = os.getenv("SQL_ENCRYPT", "no")
    SQL_TIMEOUT = int(os.getenv("SQL_TIMEOUT", "5"))

    # Guarda la ruta del script SQL que define la estructura de la base.
    SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
