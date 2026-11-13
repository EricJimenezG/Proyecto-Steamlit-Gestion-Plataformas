-- =====================================================
-- BASE DE DATOS 1: CAPTACIÓN DE CLIENTES
-- Motor: SQLite 3
-- =====================================================
PRAGMA foreign_keys = ON;

CREATE TABLE canales_captacion (
  id_canal      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre        TEXT NOT NULL UNIQUE,
  tipo TEXT NOT NULL CHECK (tipo IN ('digital','presencial','referido','telefonico')),
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1))
);

CREATE TABLE campanas (
  id_campana    INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre        TEXT NOT NULL,
  id_canal      INTEGER NOT NULL,
  fecha_inicio  TEXT NOT NULL,
  fecha_fin     TEXT NULL,
  presupuesto   NUMERIC NOT NULL DEFAULT 0,
  objetivo      TEXT NULL,
  CONSTRAINT fk_campana_canal FOREIGN KEY (id_canal) REFERENCES canales_captacion(id_canal),
  CONSTRAINT chk_campana_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE TABLE empleados (
  id_empleado   INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre        TEXT NOT NULL,
  apellidos     TEXT NOT NULL,
  correo        TEXT NOT NULL UNIQUE,
  telefono      TEXT NULL,
  puesto        TEXT NOT NULL,
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1))
);

CREATE TABLE prospectos (
  id_prospecto    INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre          TEXT NOT NULL,
  apellidos       TEXT NOT NULL,
  correo          TEXT NULL,
  telefono        TEXT NULL,
  empresa         TEXT NULL,
  id_canal        INTEGER NOT NULL,
  id_campana      INTEGER NULL,
  id_empleado     INTEGER NULL,
  estatus TEXT NOT NULL DEFAULT 'nuevo' CHECK (estatus IN ('nuevo','contactado','interesado','negociacion','convertido','descartado')),
  fecha_registro  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_prospecto_canal    FOREIGN KEY (id_canal)    REFERENCES canales_captacion(id_canal),
  CONSTRAINT fk_prospecto_campana  FOREIGN KEY (id_campana)  REFERENCES campanas(id_campana) ON DELETE SET NULL,
  CONSTRAINT fk_prospecto_empleado FOREIGN KEY (id_empleado) REFERENCES empleados(id_empleado) ON DELETE SET NULL
);

CREATE TABLE seguimientos (
  id_seguimiento  INTEGER PRIMARY KEY AUTOINCREMENT,
  id_prospecto    INTEGER NOT NULL,
  id_empleado     INTEGER NOT NULL,
  tipo_contacto TEXT NOT NULL CHECK (tipo_contacto IN ('llamada','correo','whatsapp','reunion','visita')),
  fecha_contacto  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resultado       TEXT NULL,
  notas           TEXT NULL,
  proximo_contacto TEXT NULL,
  CONSTRAINT fk_seg_prospecto FOREIGN KEY (id_prospecto) REFERENCES prospectos(id_prospecto) ON DELETE CASCADE,
  CONSTRAINT fk_seg_empleado  FOREIGN KEY (id_empleado)  REFERENCES empleados(id_empleado)
);

CREATE TABLE clientes (
  id_cliente        INTEGER PRIMARY KEY AUTOINCREMENT,
  id_prospecto      INTEGER NOT NULL UNIQUE,
  fecha_conversion  TEXT NOT NULL,
  tipo_cliente TEXT NOT NULL DEFAULT 'persona' CHECK (tipo_cliente IN ('persona','empresa')),
  rfc               TEXT NULL,
  monto_primer_compra NUMERIC NULL,
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
  CONSTRAINT fk_cliente_prospecto FOREIGN KEY (id_prospecto) REFERENCES prospectos(id_prospecto)
);

CREATE INDEX idx_prospectos_estatus ON prospectos(estatus);
CREATE INDEX idx_prospectos_campana ON prospectos(id_campana);
CREATE INDEX idx_seguimientos_fecha ON seguimientos(fecha_contacto);
