"""Operaciones relacionadas con productos y carrito de compras."""

from __future__ import annotations

from models.db import execute_non_query, execute_scalar, fetch_all, fetch_one


# Define el catalogo inicial que se carga automaticamente en la base.
PRODUCTOS_SEMILLA = [
    {
        "nombre": "Veloz Air Pro",
        "descripcion": "Tenis ligeros para running urbano con espuma reactiva y gran retorno de energia.",
        "precio": "89.90",
        "stock": 12,
        "imagen": "img/veloz-air-pro.svg",
    },
    {
        "nombre": "Costa Runner X",
        "descripcion": "Modelo respirable para entrenamientos largos con soporte suave en talon y mediopie.",
        "precio": "94.50",
        "stock": 10,
        "imagen": "img/costa-runner-x.svg",
    },
    {
        "nombre": "Solar Street Mid",
        "descripcion": "Tenis de estilo streetwear con suela firme y acabado premium para outfits diarios.",
        "precio": "99.00",
        "stock": 7,
        "imagen": "img/solar-street-mid.svg",
    },
    {
        "nombre": "Mar Azul Court",
        "descripcion": "Disenados para movimientos laterales intensos con agarre estable y amortiguacion precisa.",
        "precio": "109.99",
        "stock": 8,
        "imagen": "img/mar-azul-court.svg",
    },
    {
        "nombre": "Lava Sprint Elite",
        "descripcion": "Tenis explosivos para sesiones de velocidad con upper flexible y traccion agresiva.",
        "precio": "119.00",
        "stock": 6,
        "imagen": "img/lava-sprint-elite.svg",
    },
    {
        "nombre": "Nebula Training Max",
        "descripcion": "Opcion versatil para gimnasio y funcional con excelente soporte y comodidad diaria.",
        "precio": "102.75",
        "stock": 9,
        "imagen": "img/nebula-training-max.svg",
    },
]


def listar_productos(limit: int | None = None):
    """Devuelve todos los productos disponibles en el catalogo."""
    top_clause = f"TOP {int(limit)} " if limit else ""
    return fetch_all(
        f"""
        SELECT {top_clause}IdProducto, Nombre, Descripcion, Precio, Stock, ImagenUrl
        FROM Productos
        ORDER BY IdProducto ASC
        """
    )


def obtener_producto_por_id(product_id: int):
    """Obtiene un producto individual por su identificador."""
    return fetch_one(
        """
        SELECT IdProducto, Nombre, Descripcion, Precio, Stock, ImagenUrl
        FROM Productos
        WHERE IdProducto = ?
        """,
        [product_id],
    )


def obtener_carrito_activo(user_id: int):
    """Busca el carrito activo mas reciente del usuario."""
    return fetch_one(
        """
        SELECT TOP 1 IdCarrito, IdUsuario, Estado, FechaCreacion
        FROM Carrito
        WHERE IdUsuario = ? AND Estado = 'ACTIVO'
        ORDER BY IdCarrito DESC
        """,
        [user_id],
    )


def obtener_o_crear_carrito(user_id: int):
    """Recupera el carrito activo o crea uno nuevo si todavia no existe."""
    carrito = obtener_carrito_activo(user_id)

    if carrito:
        return carrito

    cart_id = execute_scalar(
        """
        INSERT INTO Carrito (IdUsuario, Estado, FechaCreacion)
        OUTPUT INSERTED.IdCarrito
        VALUES (?, 'ACTIVO', GETDATE())
        """,
        [user_id],
    )
    return fetch_one(
        """
        SELECT IdCarrito, IdUsuario, Estado, FechaCreacion
        FROM Carrito
        WHERE IdCarrito = ?
        """,
        [cart_id],
    )


def agregar_al_carrito(user_id: int, product_id: int, cantidad: int):
    """Agrega un producto al carrito, respetando el stock disponible."""
    producto = obtener_producto_por_id(product_id)

    if not producto:
        return False, "El producto solicitado no existe."

    cantidad = max(1, int(cantidad))
    carrito = obtener_o_crear_carrito(user_id)
    detalle_existente = fetch_one(
        """
        SELECT IdDetalleCarrito, Cantidad
        FROM DetalleCarrito
        WHERE IdCarrito = ? AND IdProducto = ?
        """,
        [carrito["IdCarrito"], product_id],
    )

    cantidad_actual = detalle_existente["Cantidad"] if detalle_existente else 0

    if cantidad_actual + cantidad > producto["Stock"]:
        return False, "No hay stock suficiente para la cantidad solicitada."

    if detalle_existente:
        execute_non_query(
            """
            UPDATE DetalleCarrito
            SET Cantidad = Cantidad + ?
            WHERE IdDetalleCarrito = ?
            """,
            [cantidad, detalle_existente["IdDetalleCarrito"]],
        )
    else:
        execute_non_query(
            """
            INSERT INTO DetalleCarrito (IdCarrito, IdProducto, Cantidad, PrecioUnitario)
            VALUES (?, ?, ?, ?)
            """,
            [carrito["IdCarrito"], product_id, cantidad, producto["Precio"]],
        )

    return True, f"{producto['Nombre']} se agrego correctamente al carrito."


def obtener_items_carrito(user_id: int):
    """Obtiene los productos guardados en el carrito activo."""
    carrito = obtener_carrito_activo(user_id)

    if not carrito:
        return []

    return fetch_all(
        """
        SELECT
            dc.IdDetalleCarrito,
            dc.Cantidad,
            dc.PrecioUnitario,
            CAST(dc.Cantidad * dc.PrecioUnitario AS DECIMAL(10, 2)) AS Subtotal,
            p.IdProducto,
            p.Nombre,
            p.Descripcion,
            p.ImagenUrl,
            p.Stock
        FROM DetalleCarrito AS dc
        INNER JOIN Productos AS p ON p.IdProducto = dc.IdProducto
        WHERE dc.IdCarrito = ?
        ORDER BY dc.IdDetalleCarrito DESC
        """,
        [carrito["IdCarrito"]],
    )


def obtener_total_carrito(user_id: int):
    """Calcula el total monetario del carrito activo."""
    carrito = obtener_carrito_activo(user_id)

    if not carrito:
        return 0

    total = execute_scalar(
        """
        SELECT CAST(COALESCE(SUM(Cantidad * PrecioUnitario), 0) AS DECIMAL(10, 2))
        FROM DetalleCarrito
        WHERE IdCarrito = ?
        """,
        [carrito["IdCarrito"]],
    )
    return total or 0


def contar_items_carrito(user_id: int):
    """Cuenta cuantas unidades hay en el carrito activo."""
    carrito = obtener_carrito_activo(user_id)

    if not carrito:
        return 0

    total_items = execute_scalar(
        """
        SELECT COALESCE(SUM(Cantidad), 0)
        FROM DetalleCarrito
        WHERE IdCarrito = ?
        """,
        [carrito["IdCarrito"]],
    )
    return int(total_items or 0)


def eliminar_item_carrito(user_id: int, detail_id: int):
    """Elimina un item puntual del carrito del usuario."""
    carrito = obtener_carrito_activo(user_id)

    if not carrito:
        return False, "No se encontro un carrito activo para eliminar productos."

    detalle = fetch_one(
        """
        SELECT IdDetalleCarrito
        FROM DetalleCarrito
        WHERE IdDetalleCarrito = ? AND IdCarrito = ?
        """,
        [detail_id, carrito["IdCarrito"]],
    )

    if not detalle:
        return False, "El producto ya no existe dentro de tu carrito."

    execute_non_query(
        """
        DELETE FROM DetalleCarrito
        WHERE IdDetalleCarrito = ? AND IdCarrito = ?
        """,
        [detail_id, carrito["IdCarrito"]],
    )
    return True, "Producto eliminado del carrito."


def seed_default_products():
    """Inserta el catalogo base solo si todavia no existe en la base."""
    for producto in PRODUCTOS_SEMILLA:
        existente = fetch_one(
            """
            SELECT IdProducto
            FROM Productos
            WHERE Nombre = ?
            """,
            [producto["nombre"]],
        )

        if not existente:
            execute_non_query(
                """
                INSERT INTO Productos (Nombre, Descripcion, Precio, Stock, ImagenUrl)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    producto["nombre"],
                    producto["descripcion"],
                    producto["precio"],
                    producto["stock"],
                    producto["imagen"],
                ],
            )
