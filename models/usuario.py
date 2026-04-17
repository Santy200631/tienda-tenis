"""Operaciones relacionadas con usuarios y autenticacion."""

from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from models.db import execute_scalar, fetch_one


def obtener_usuario_por_id(user_id: int):
    """Busca un usuario por su identificador interno."""
    return fetch_one(
        """
        SELECT IdUsuario, NombreUsuario, EsAdmin, FechaRegistro
        FROM Usuarios
        WHERE IdUsuario = ?
        """,
        [user_id],
    )


def obtener_usuario_por_nombre(nombre_usuario: str):
    """Busca un usuario por su nombre de acceso."""
    return fetch_one(
        """
        SELECT IdUsuario, NombreUsuario, ContrasenaHash, EsAdmin, FechaRegistro
        FROM Usuarios
        WHERE NombreUsuario = ?
        """,
        [nombre_usuario],
    )


def registrar_usuario(nombre_usuario: str, contrasena: str, es_admin: bool = False):
    """Registra un usuario nuevo si el nombre todavia no existe."""
    username = nombre_usuario.strip()

    if not username:
        return False, "Debes indicar un nombre de usuario."

    if obtener_usuario_por_nombre(username):
        return False, "Ese nombre de usuario ya esta registrado."

    user_id = execute_scalar(
        """
        INSERT INTO Usuarios (NombreUsuario, ContrasenaHash, EsAdmin, FechaRegistro)
        OUTPUT INSERTED.IdUsuario
        VALUES (?, ?, ?, GETDATE())
        """,
        [username, generate_password_hash(contrasena), int(es_admin)],
    )
    return True, user_id


def autenticar_usuario(nombre_usuario: str, contrasena: str):
    """Valida las credenciales y devuelve el usuario autenticado."""
    usuario = obtener_usuario_por_nombre(nombre_usuario.strip())

    if not usuario:
        return None

    if not check_password_hash(usuario["ContrasenaHash"], contrasena):
        return None

    usuario.pop("ContrasenaHash", None)
    return usuario


def seed_default_users():
    """Crea los usuarios de prueba solicitados si no existen."""
    default_users = [
        {"nombre_usuario": "usuario1", "contrasena": "1234", "es_admin": False},
        {"nombre_usuario": "admin", "contrasena": "admin123", "es_admin": True},
    ]

    for user_data in default_users:
        if not obtener_usuario_por_nombre(user_data["nombre_usuario"]):
            registrar_usuario(
                user_data["nombre_usuario"],
                user_data["contrasena"],
                user_data["es_admin"],
            )
