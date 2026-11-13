-- =====================================================
-- BASE DE DATOS 2: MERCADO LIBRE (marketplace)
-- Motor: SQLite 3
-- =====================================================
PRAGMA foreign_keys = ON;

CREATE TABLE usuarios (
  id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
  nickname        TEXT NOT NULL UNIQUE,
  nombre          TEXT NOT NULL,
  apellidos       TEXT NOT NULL,
  correo          TEXT NOT NULL UNIQUE,
  telefono        TEXT NULL,
  contrasena_hash TEXT NOT NULL,
  tipo_usuario TEXT NOT NULL DEFAULT 'comprador' CHECK (tipo_usuario IN ('comprador','vendedor','ambos')),
  reputacion      NUMERIC NOT NULL DEFAULT 0,
  fecha_registro  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1))
);

CREATE TABLE direcciones (
  id_direccion  INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario    INTEGER NOT NULL,
  calle         TEXT NOT NULL,
  num_exterior  TEXT NOT NULL,
  num_interior  TEXT NULL,
  colonia       TEXT NOT NULL,
  ciudad        TEXT NOT NULL,
  estado        TEXT NOT NULL,
  codigo_postal TEXT NOT NULL,
  referencias   TEXT NULL,
  es_principal INTEGER NOT NULL DEFAULT 0 CHECK (es_principal IN (0,1)),
  CONSTRAINT fk_dir_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

CREATE TABLE categorias (
  id_categoria        INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre              TEXT NOT NULL,
  id_categoria_padre  INTEGER NULL,
  CONSTRAINT fk_cat_padre FOREIGN KEY (id_categoria_padre) REFERENCES categorias(id_categoria) ON DELETE SET NULL
);

CREATE TABLE publicaciones (
  id_publicacion    INTEGER PRIMARY KEY AUTOINCREMENT,
  id_vendedor       INTEGER NOT NULL,
  id_categoria      INTEGER NOT NULL,
  titulo            TEXT NOT NULL,
  descripcion       TEXT NULL,
  precio            NUMERIC NOT NULL CHECK (precio >= 0),
  stock             INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
  condicion TEXT NOT NULL DEFAULT 'nuevo' CHECK (condicion IN ('nuevo','usado','reacondicionado')),
  tipo_publicacion TEXT NOT NULL DEFAULT 'clasica' CHECK (tipo_publicacion IN ('gratuita','clasica','premium')),
  envio_gratis INTEGER NOT NULL DEFAULT 0 CHECK (envio_gratis IN (0,1)),
  estatus TEXT NOT NULL DEFAULT 'activa' CHECK (estatus IN ('activa','pausada','finalizada')),
  fecha_publicacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pub_vendedor  FOREIGN KEY (id_vendedor)  REFERENCES usuarios(id_usuario),
  CONSTRAINT fk_pub_categoria FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
);

CREATE TABLE imagenes_publicacion (
  id_imagen      INTEGER PRIMARY KEY AUTOINCREMENT,
  id_publicacion INTEGER NOT NULL,
  url            TEXT NOT NULL,
  orden          INTEGER NOT NULL DEFAULT 1,
  CONSTRAINT fk_img_pub FOREIGN KEY (id_publicacion) REFERENCES publicaciones(id_publicacion) ON DELETE CASCADE
);

CREATE TABLE favoritos (
  id_usuario      INTEGER NOT NULL,
  id_publicacion  INTEGER NOT NULL,
  fecha_agregado  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_usuario, id_publicacion),
  CONSTRAINT fk_fav_usuario FOREIGN KEY (id_usuario)     REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
  CONSTRAINT fk_fav_pub     FOREIGN KEY (id_publicacion) REFERENCES publicaciones(id_publicacion) ON DELETE CASCADE
);

CREATE TABLE preguntas (
  id_pregunta     INTEGER PRIMARY KEY AUTOINCREMENT,
  id_publicacion  INTEGER NOT NULL,
  id_usuario      INTEGER NOT NULL,
  pregunta        TEXT NOT NULL,
  respuesta       TEXT NULL,
  fecha_pregunta  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_respuesta TEXT NULL,
  CONSTRAINT fk_preg_pub     FOREIGN KEY (id_publicacion) REFERENCES publicaciones(id_publicacion) ON DELETE CASCADE,
  CONSTRAINT fk_preg_usuario FOREIGN KEY (id_usuario)     REFERENCES usuarios(id_usuario)
);

CREATE TABLE pedidos (
  id_pedido            INTEGER PRIMARY KEY AUTOINCREMENT,
  id_comprador         INTEGER NOT NULL,
  id_direccion_envio   INTEGER NOT NULL,
  fecha_pedido         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estatus TEXT NOT NULL DEFAULT 'pendiente' CHECK (estatus IN ('pendiente','pagado','enviado','entregado','cancelado','devuelto')),
  total                NUMERIC NOT NULL DEFAULT 0,
  CONSTRAINT fk_ped_comprador FOREIGN KEY (id_comprador)       REFERENCES usuarios(id_usuario),
  CONSTRAINT fk_ped_direccion FOREIGN KEY (id_direccion_envio) REFERENCES direcciones(id_direccion)
);

CREATE TABLE detalle_pedido (
  id_detalle       INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pedido        INTEGER NOT NULL,
  id_publicacion   INTEGER NOT NULL,
  cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
  precio_unitario  NUMERIC NOT NULL,
  CONSTRAINT fk_det_pedido FOREIGN KEY (id_pedido)      REFERENCES pedidos(id_pedido) ON DELETE CASCADE,
  CONSTRAINT fk_det_pub    FOREIGN KEY (id_publicacion) REFERENCES publicaciones(id_publicacion)
);

CREATE TABLE pagos (
  id_pago      INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pedido    INTEGER NOT NULL,
  metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('tarjeta_credito','tarjeta_debito','mercado_pago','oxxo','transferencia')),
  monto        NUMERIC NOT NULL,
  estatus TEXT NOT NULL DEFAULT 'pendiente' CHECK (estatus IN ('pendiente','aprobado','rechazado','reembolsado')),
  fecha_pago   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pago_pedido FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
);

CREATE TABLE envios (
  id_envio       INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pedido      INTEGER NOT NULL UNIQUE,
  paqueteria     TEXT NOT NULL,
  numero_guia    TEXT NULL UNIQUE,
  estatus TEXT NOT NULL DEFAULT 'preparando' CHECK (estatus IN ('preparando','en_camino','entregado','devuelto')),
  fecha_envio    TEXT NULL,
  fecha_entrega  TEXT NULL,
  CONSTRAINT fk_envio_pedido FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido)
);

CREATE TABLE resenas (
  id_resena    INTEGER PRIMARY KEY AUTOINCREMENT,
  id_detalle   INTEGER NOT NULL UNIQUE,
  puntuacion   INTEGER NOT NULL CHECK (puntuacion BETWEEN 1 AND 5),
  comentario   TEXT NULL,
  fecha_resena TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_resena_detalle FOREIGN KEY (id_detalle) REFERENCES detalle_pedido(id_detalle) ON DELETE CASCADE
);

CREATE INDEX idx_pub_categoria ON publicaciones(id_categoria);
CREATE INDEX idx_pub_vendedor  ON publicaciones(id_vendedor);
CREATE INDEX idx_ped_comprador ON pedidos(id_comprador);
