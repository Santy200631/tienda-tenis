-- Crea la base de datos si todavia no existe.
IF DB_ID(N'PuraTenisDB') IS NULL
BEGIN
    CREATE DATABASE PuraTenisDB;
END;
GO

-- Selecciona la base principal del proyecto.
USE PuraTenisDB;
GO

-- Crea la tabla de usuarios para autenticacion y perfiles basicos.
IF OBJECT_ID(N'dbo.Usuarios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Usuarios
    (
        IdUsuario INT IDENTITY(1,1) PRIMARY KEY,
        NombreUsuario NVARCHAR(50) NOT NULL UNIQUE,
        ContrasenaHash NVARCHAR(255) NOT NULL,
        EsAdmin BIT NOT NULL DEFAULT 0,
        FechaRegistro DATETIME NOT NULL DEFAULT GETDATE()
    );
END;
GO

-- Crea la tabla de productos que alimenta el catalogo web.
IF OBJECT_ID(N'dbo.Productos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Productos
    (
        IdProducto INT IDENTITY(1,1) PRIMARY KEY,
        Nombre NVARCHAR(120) NOT NULL,
        Descripcion NVARCHAR(500) NOT NULL,
        Precio DECIMAL(10,2) NOT NULL CHECK (Precio >= 0),
        Stock INT NOT NULL CHECK (Stock >= 0),
        ImagenUrl NVARCHAR(255) NOT NULL
    );
END;
GO

-- Crea la tabla que representa el carrito general de cada usuario.
IF OBJECT_ID(N'dbo.Carrito', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Carrito
    (
        IdCarrito INT IDENTITY(1,1) PRIMARY KEY,
        IdUsuario INT NOT NULL,
        Estado NVARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
        FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_Carrito_Usuarios
            FOREIGN KEY (IdUsuario) REFERENCES dbo.Usuarios(IdUsuario)
    );
END;
GO

-- Crea el detalle de productos guardados dentro de cada carrito.
IF OBJECT_ID(N'dbo.DetalleCarrito', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DetalleCarrito
    (
        IdDetalleCarrito INT IDENTITY(1,1) PRIMARY KEY,
        IdCarrito INT NOT NULL,
        IdProducto INT NOT NULL,
        Cantidad INT NOT NULL CHECK (Cantidad > 0),
        PrecioUnitario DECIMAL(10,2) NOT NULL CHECK (PrecioUnitario >= 0),
        CONSTRAINT FK_DetalleCarrito_Carrito
            FOREIGN KEY (IdCarrito) REFERENCES dbo.Carrito(IdCarrito),
        CONSTRAINT FK_DetalleCarrito_Productos
            FOREIGN KEY (IdProducto) REFERENCES dbo.Productos(IdProducto)
    );
END;
GO

-- Crea indices utiles para mejorar busquedas habituales del sistema.
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_Usuarios_NombreUsuario'
      AND object_id = OBJECT_ID(N'dbo.Usuarios')
)
BEGIN
    CREATE INDEX IX_Usuarios_NombreUsuario ON dbo.Usuarios(NombreUsuario);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_Carrito_IdUsuario'
      AND object_id = OBJECT_ID(N'dbo.Carrito')
)
BEGIN
    CREATE INDEX IX_Carrito_IdUsuario ON dbo.Carrito(IdUsuario);
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_DetalleCarrito_IdCarrito'
      AND object_id = OBJECT_ID(N'dbo.DetalleCarrito')
)
BEGIN
    CREATE INDEX IX_DetalleCarrito_IdCarrito ON dbo.DetalleCarrito(IdCarrito);
END;
GO
