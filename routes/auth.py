"""Rutas relacionadas con autenticacion y sesiones."""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.usuario import autenticar_usuario, obtener_usuario_por_id, registrar_usuario


# Define el blueprint dedicado a autenticacion.
auth_bp = Blueprint("auth", __name__)


def login_required(view_function):
    """Protege rutas que requieren una sesion autenticada."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesion para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return view_function(*args, **kwargs)

    return wrapped_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Permite crear nuevas cuentas de usuario."""
    if session.get("user_id"):
        return redirect(url_for("productos.ver_catalogo"))

    if request.method == "POST":
        nombre_usuario = request.form.get("nombre_usuario", "").strip()
        contrasena = request.form.get("contrasena", "")
        confirmar_contrasena = request.form.get("confirmar_contrasena", "")

        if not nombre_usuario or not contrasena:
            flash("Completa todos los campos obligatorios.", "danger")
        elif len(contrasena) < 4:
            flash("La contrasena debe tener al menos 4 caracteres.", "danger")
        elif contrasena != confirmar_contrasena:
            flash("Las contrasenas no coinciden.", "danger")
        else:
            success, result = registrar_usuario(nombre_usuario, contrasena)

            if success:
                usuario = obtener_usuario_por_id(result)
                session.clear()
                session["user_id"] = usuario["IdUsuario"]
                session["username"] = usuario["NombreUsuario"]
                session["is_admin"] = bool(usuario["EsAdmin"])
                flash("Tu cuenta fue creada con exito.", "success")
                return redirect(url_for("productos.ver_catalogo"))

            flash(result, "danger")

    return render_template("register.html", title="Crear cuenta")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Permite iniciar sesion con usuarios existentes."""
    if session.get("user_id"):
        return redirect(url_for("productos.ver_catalogo"))

    if request.method == "POST":
        nombre_usuario = request.form.get("nombre_usuario", "").strip()
        contrasena = request.form.get("contrasena", "")
        usuario = autenticar_usuario(nombre_usuario, contrasena)

        if usuario:
            session.clear()
            session["user_id"] = usuario["IdUsuario"]
            session["username"] = usuario["NombreUsuario"]
            session["is_admin"] = bool(usuario["EsAdmin"])
            flash(f"Bienvenido de nuevo, {usuario['NombreUsuario']}.", "success")
            return redirect(url_for("productos.ver_catalogo"))

        flash("Credenciales invalidas. Intenta nuevamente.", "danger")

    return render_template("login.html", title="Iniciar sesion")


@auth_bp.route("/logout")
def logout():
    """Cierra la sesion del usuario actual."""
    session.clear()
    flash("Sesion cerrada correctamente.", "info")
    return redirect(url_for("productos.inicio"))
