-- =====================================================
-- BASE DE DATOS 4: VENTAS A NIVEL REPÚBLICA
-- Motor: SQLite 3
-- =====================================================
PRAGMA foreign_keys = ON;

CREATE TABLE zonas (
  id_zona  INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre   TEXT NOT NULL UNIQUE   -- Norte, Centro, Sur, Bajío, etc.
);

CREATE TABLE estados (
  id_estado  INTEGER PRIMARY KEY AUTOINCREMENT,
  clave      TEXT NOT NULL UNIQUE,
  nombre     TEXT NOT NULL UNIQUE,
  id_zona    INTEGER NOT NULL,
  CONSTRAINT fk_estado_zona FOREIGN KEY (id_zona) REFERENCES zonas(id_zona)
);

CREATE TABLE sucursales (
  id_sucursal  INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre       TEXT NOT NULL,
  id_estado    INTEGER NOT NULL,
  ciudad       TEXT NOT NULL,
  direccion    TEXT NOT NULL,
  telefono     TEXT NULL,
  fecha_apertura TEXT NULL,
  activa INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0,1)),
  CONSTRAINT fk_suc_estado FOREIGN KEY (id_estado) REFERENCES estados(id_estado)
);

CREATE TABLE empleados (
  id_empleado        INTEGER PRIMARY KEY AUTOINCREMENT,
  id_sucursal        INTEGER NOT NULL,
  nombre             TEXT NOT NULL,
  apellidos          TEXT NOT NULL,
  correo             TEXT NOT NULL UNIQUE,
  puesto TEXT NOT NULL DEFAULT 'vendedor' CHECK (puesto IN ('vendedor','cajero','gerente','almacenista')),
  fecha_contratacion TEXT NOT NULL,
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
  CONSTRAINT fk_emp_sucursal FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
);

CREATE TABLE clientes (
  id_cliente      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre          TEXT NOT NULL,
  apellidos       TEXT NOT NULL,
  correo          TEXT NULL,
  telefono        TEXT NULL,
  rfc             TEXT NULL,
  id_estado       INTEGER NOT NULL,
  ciudad          TEXT NULL,
  fecha_registro  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cli_estado FOREIGN KEY (id_estado) REFERENCES estados(id_estado)
);

CREATE TABLE categorias (
  id_categoria  INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre        TEXT NOT NULL UNIQUE
);

CREATE TABLE productos (
  id_producto      INTEGER PRIMARY KEY AUTOINCREMENT,
  sku              TEXT NOT NULL UNIQUE,
  nombre           TEXT NOT NULL,
  id_categoria     INTEGER NOT NULL,
  precio_unitario  NUMERIC NOT NULL CHECK (precio_unitario >= 0),
  costo            NUMERIC NOT NULL CHECK (costo >= 0),
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
  CONSTRAINT fk_prod_categoria FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
);

CREATE TABLE inventario (
  id_sucursal   INTEGER NOT NULL,
  id_producto   INTEGER NOT NULL,
  existencias   INTEGER NOT NULL DEFAULT 0 CHECK (existencias >= 0),
  stock_minimo  INTEGER NOT NULL DEFAULT 5,
  PRIMARY KEY (id_sucursal, id_producto),
  CONSTRAINT fk_inv_sucursal FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal),
  CONSTRAINT fk_inv_producto FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
);

CREATE TABLE ventas (
  id_venta     INTEGER PRIMARY KEY AUTOINCREMENT,
  folio        TEXT NOT NULL UNIQUE,
  id_sucursal  INTEGER NOT NULL,
  id_empleado  INTEGER NOT NULL,
  id_cliente   INTEGER NULL,
  fecha_venta  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('efectivo','tarjeta_credito','tarjeta_debito','transferencia')),
  subtotal     NUMERIC NOT NULL DEFAULT 0,
  iva          NUMERIC NOT NULL DEFAULT 0,
  total        NUMERIC NOT NULL DEFAULT 0,
  estatus TEXT NOT NULL DEFAULT 'completada' CHECK (estatus IN ('completada','cancelada','devuelta')),
  CONSTRAINT fk_venta_sucursal FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal),
  CONSTRAINT fk_venta_empleado FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado),
  CONSTRAINT fk_venta_cliente  FOREIGN KEY (id_cliente)  REFERENCES clientes(id_cliente) ON DELETE SET NULL
);

CREATE TABLE detalle_venta (
  id_detalle       INTEGER PRIMARY KEY AUTOINCREMENT,
  id_venta         INTEGER NOT NULL,
  id_producto      INTEGER NOT NULL,
  cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
  precio_unitario  NUMERIC NOT NULL,
  descuento        NUMERIC NOT NULL DEFAULT 0,
  CONSTRAINT fk_det_venta    FOREIGN KEY (id_venta)    REFERENCES ventas(id_venta) ON DELETE CASCADE,
  CONSTRAINT fk_det_producto FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
);

CREATE TABLE metas_ventas (
  id_meta      INTEGER PRIMARY KEY AUTOINCREMENT,
  id_sucursal  INTEGER NOT NULL,
  anio         INTEGER NOT NULL,
  mes          INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
  meta_monto   NUMERIC NOT NULL,
  UNIQUE (id_sucursal, anio, mes),
  CONSTRAINT fk_meta_sucursal FOREIGN KEY (id_sucursal) REFERENCES sucursales(id_sucursal)
);

CREATE INDEX idx_ventas_fecha    ON ventas(fecha_venta);
CREATE INDEX idx_ventas_sucursal ON ventas(id_sucursal);
CREATE INDEX idx_det_producto    ON detalle_venta(id_producto);
