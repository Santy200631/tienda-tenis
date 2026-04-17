"""Rutas relacionadas con home, productos y carrito."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models.producto import (
    agregar_al_carrito,
    eliminar_item_carrito,
    listar_productos,
    obtener_items_carrito,
    obtener_producto_por_id,
    obtener_total_carrito,
)
from routes.auth import login_required


# Define el blueprint principal del catalogo.
productos_bp = Blueprint("productos", __name__)


@productos_bp.route("/")
def inicio():
    """Renderiza la pagina de inicio con una seleccion destacada."""
    productos_destacados = listar_productos(limit=3)
    return render_template(
        "index.html",
        title="Inicio",
        productos_destacados=productos_destacados,
    )


@productos_bp.route("/productos")
def ver_catalogo():
    """Muestra el listado completo de tenis disponibles."""
    return render_template(
        "productos.html",
        title="Catalogo de tenis",
        productos=listar_productos(),
        producto_seleccionado=None,
    )


@productos_bp.route("/productos/<int:product_id>")
def ver_detalle_producto(product_id: int):
    """Muestra el mismo catalogo con un producto resaltado en detalle."""
    productos = listar_productos()
    producto_seleccionado = obtener_producto_por_id(product_id)

    if not producto_seleccionado:
        flash("El producto solicitado no esta disponible.", "warning")
        return redirect(url_for("productos.ver_catalogo"))

    return render_template(
        "productos.html",
        title=producto_seleccionado["Nombre"],
        productos=productos,
        producto_seleccionado=producto_seleccionado,
    )


@productos_bp.route("/carrito")
@login_required
def ver_carrito():
    """Muestra el carrito activo del usuario autenticado."""
    user_id = session["user_id"]
    items = obtener_items_carrito(user_id)
    total = obtener_total_carrito(user_id)

    return render_template(
        "carrito.html",
        title="Mi carrito",
        items=items,
        total=total,
    )


@productos_bp.route("/carrito/agregar/<int:product_id>", methods=["POST"])
@login_required
def agregar_carrito(product_id: int):
    """Agrega una cantidad de un producto al carrito del usuario."""
    try:
        cantidad = int(request.form.get("cantidad", 1))
    except ValueError:
        cantidad = 1

    success, message = agregar_al_carrito(session["user_id"], product_id, cantidad)
    flash(message, "success" if success else "danger")

    redirect_to = request.form.get("redirect_to", "").strip()
    if not redirect_to.startswith("/"):
        redirect_to = url_for("productos.ver_catalogo")

    return redirect(redirect_to)


@productos_bp.route("/carrito/eliminar/<int:detail_id>", methods=["POST"])
@login_required
def eliminar_del_carrito(detail_id: int):
    """Elimina un item individual del carrito."""
    success, message = eliminar_item_carrito(session["user_id"], detail_id)
    flash(message, "success" if success else "warning")
    return redirect(url_for("productos.ver_carrito"))
