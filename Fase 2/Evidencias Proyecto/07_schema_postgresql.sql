-- Sistema Inteligente de Gestión y Optimización de Inventario
-- Esquema base para PostgreSQL - APT122
-- Nota: adaptar nombres a los modelos Django definitivos.

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255)
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER NOT NULL REFERENCES roles(id),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    rut VARCHAR(30),
    email VARCHAR(150),
    telefono VARCHAR(30),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(80) NOT NULL UNIQUE,
    codigo_qr VARCHAR(255) UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    unidad_medida VARCHAR(30) NOT NULL DEFAULT 'unidad',
    precio_referencia NUMERIC(12,2) DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cotizaciones (
    id SERIAL PRIMARY KEY,
    proveedor_id INTEGER NOT NULL REFERENCES proveedores(id),
    numero VARCHAR(60) NOT NULL UNIQUE,
    moneda VARCHAR(10) NOT NULL DEFAULT 'CLP',
    estado VARCHAR(30) NOT NULL DEFAULT 'REGISTRADA',
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    observaciones TEXT
);

CREATE TABLE detalle_cotizacion (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    cantidad NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0)
);

CREATE TABLE stock (
    producto_id INTEGER PRIMARY KEY REFERENCES productos(id) ON DELETE CASCADE,
    cantidad NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (cantidad >= 0),
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entradas (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

CREATE TABLE detalle_entrada (
    id SERIAL PRIMARY KEY,
    entrada_id INTEGER NOT NULL REFERENCES entradas(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    cantidad NUMERIC(12,2) NOT NULL CHECK (cantidad > 0)
);

CREATE TABLE salidas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

CREATE TABLE detalle_salida (
    id SERIAL PRIMARY KEY,
    salida_id INTEGER NOT NULL REFERENCES salidas(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    cantidad NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    codigo_qr VARCHAR(255)
);

CREATE TABLE movimientos (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ENTRADA','SALIDA')),
    cantidad NUMERIC(12,2) NOT NULL CHECK (cantidad > 0),
    referencia_tipo VARCHAR(30),
    referencia_id INTEGER,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT
);

CREATE INDEX idx_movimientos_producto_fecha
ON movimientos(producto_id, fecha DESC);

CREATE INDEX idx_cotizaciones_proveedor
ON cotizaciones(proveedor_id);

CREATE INDEX idx_detalle_cotizacion_producto
ON detalle_cotizacion(producto_id);

-- Regla de negocio:
-- La aplicación Django/DRF debe impedir la creación de una entrada
-- si la cotización asociada no existe o no es válida.
-- La aplicación también debe validar stock antes de registrar una salida.
