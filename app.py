"""Punto de entrada principal de la aplicacion PURA TENIS."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, session

from config import Config
from models.db import DatabaseConnectionError, initialize_database
from models.producto import contar_items_carrito
from models.usuario import obtener_usuario_por_id
from routes.auth import auth_bp
from routes.productos import productos_bp


def create_app():
    """Crea y configura la aplicacion Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registra los modulos de autenticacion y catalogo.
    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)

    # Prepara la base de datos y los datos iniciales al arrancar la app.
    try:
        with app.app_context():
            initialize_database()
        app.config["DATABASE_ERROR"] = None
    except DatabaseConnectionError as error:
        app.config["DATABASE_ERROR"] = str(error)
        app.logger.exception("No fue posible inicializar la base de datos.")
    except Exception as error:
        app.config["DATABASE_ERROR"] = (
            "Se produjo un error inesperado al preparar la base de datos: "
            f"{error}"
        )
        app.logger.exception("Ocurrio un error inesperado durante la inicializacion.")

    @app.context_processor
    def inject_shared_context():
        """Expone datos globales para la navegacion y el layout general."""
        user_id = session.get("user_id")
        current_user = None
        cart_count = 0

        if user_id and not app.config.get("DATABASE_ERROR"):
            try:
                current_user = obtener_usuario_por_id(user_id)
                cart_count = contar_items_carrito(user_id)
            except Exception:
                app.logger.exception("No fue posible cargar el contexto del usuario.")

        return {
            "current_user": current_user,
            "cart_count": cart_count,
            "current_year": datetime.now().year,
            "database_error": app.config.get("DATABASE_ERROR"),
        }

    @app.template_filter("currency")
    def currency_filter(value):
        """Convierte valores numericos a un formato monetario legible."""
        try:
            amount = Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            amount = Decimal("0")
        return f"${amount:,.2f}"

    @app.errorhandler(404)
    def not_found(error):
        """Muestra una vista amigable cuando la ruta no existe."""
        return (
            render_template("index.html", productos_destacados=[], not_found=True),
            404,
        )

    @app.errorhandler(500)
    def internal_error(error):
        """Muestra una vista de respaldo para errores internos."""
        return (
            render_template("index.html", productos_destacados=[], server_error=True),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    # Ejecuta la app exactamente en el host y puerto solicitados.
    app.run(host="127.0.0.1", port=5000, debug=False)
