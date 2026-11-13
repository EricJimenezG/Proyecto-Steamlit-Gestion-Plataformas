-- =====================================================
-- BASE DE DATOS 3: E-LEARNING - CURSOS
-- Motor: SQLite 3
-- =====================================================
PRAGMA foreign_keys = ON;

CREATE TABLE usuarios (
  id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre          TEXT NOT NULL,
  apellidos       TEXT NOT NULL,
  correo          TEXT NOT NULL UNIQUE,
  contrasena_hash TEXT NOT NULL,
  rol TEXT NOT NULL DEFAULT 'estudiante' CHECK (rol IN ('estudiante','instructor','administrador')),
  biografia       TEXT NULL,
  fecha_registro  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1))
);

CREATE TABLE categorias_curso (
  id_categoria  INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre        TEXT NOT NULL UNIQUE,
  descripcion   TEXT NULL
);

CREATE TABLE cursos (
  id_curso        INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo          TEXT NOT NULL,
  descripcion     TEXT NULL,
  id_categoria    INTEGER NOT NULL,
  id_instructor   INTEGER NOT NULL,
  nivel TEXT NOT NULL DEFAULT 'basico' CHECK (nivel IN ('basico','intermedio','avanzado')),
  idioma          TEXT NOT NULL DEFAULT 'Español',
  precio          NUMERIC NOT NULL DEFAULT 0 CHECK (precio >= 0),
  duracion_horas  NUMERIC NULL,
  estatus TEXT NOT NULL DEFAULT 'borrador' CHECK (estatus IN ('borrador','publicado','archivado')),
  fecha_creacion  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_curso_categoria  FOREIGN KEY (id_categoria)  REFERENCES categorias_curso(id_categoria),
  CONSTRAINT fk_curso_instructor FOREIGN KEY (id_instructor) REFERENCES usuarios(id_usuario)
);

CREATE TABLE modulos (
  id_modulo  INTEGER PRIMARY KEY AUTOINCREMENT,
  id_curso   INTEGER NOT NULL,
  titulo     TEXT NOT NULL,
  orden      INTEGER NOT NULL,
  UNIQUE (id_curso, orden),
  CONSTRAINT fk_modulo_curso FOREIGN KEY (id_curso) REFERENCES cursos(id_curso) ON DELETE CASCADE
);

CREATE TABLE lecciones (
  id_leccion     INTEGER PRIMARY KEY AUTOINCREMENT,
  id_modulo      INTEGER NOT NULL,
  titulo         TEXT NOT NULL,
  tipo TEXT NOT NULL DEFAULT 'video' CHECK (tipo IN ('video','lectura','archivo','quiz')),
  url_contenido  TEXT NULL,
  duracion_min   INTEGER NULL,
  orden          INTEGER NOT NULL,
  UNIQUE (id_modulo, orden),
  CONSTRAINT fk_leccion_modulo FOREIGN KEY (id_modulo) REFERENCES modulos(id_modulo) ON DELETE CASCADE
);

CREATE TABLE inscripciones (
  id_inscripcion      INTEGER PRIMARY KEY AUTOINCREMENT,
  id_usuario          INTEGER NOT NULL,
  id_curso            INTEGER NOT NULL,
  fecha_inscripcion   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  progreso            NUMERIC NOT NULL DEFAULT 0 CHECK (progreso BETWEEN 0 AND 100),
  estatus TEXT NOT NULL DEFAULT 'activa' CHECK (estatus IN ('activa','completada','abandonada')),
  fecha_finalizacion  TEXT NULL,
  UNIQUE (id_usuario, id_curso),
  CONSTRAINT fk_insc_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
  CONSTRAINT fk_insc_curso   FOREIGN KEY (id_curso)   REFERENCES cursos(id_curso)
);

CREATE TABLE progreso_lecciones (
  id_inscripcion  INTEGER NOT NULL,
  id_leccion      INTEGER NOT NULL,
  completada INTEGER NOT NULL DEFAULT 0 CHECK (completada IN (0,1)),
  fecha_completada TEXT NULL,
  PRIMARY KEY (id_inscripcion, id_leccion),
  CONSTRAINT fk_prog_insc    FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion) ON DELETE CASCADE,
  CONSTRAINT fk_prog_leccion FOREIGN KEY (id_leccion)     REFERENCES lecciones(id_leccion) ON DELETE CASCADE
);

CREATE TABLE evaluaciones (
  id_evaluacion   INTEGER PRIMARY KEY AUTOINCREMENT,
  id_modulo       INTEGER NOT NULL,
  titulo          TEXT NOT NULL,
  puntaje_minimo  NUMERIC NOT NULL DEFAULT 70,
  intentos_max    INTEGER NOT NULL DEFAULT 3,
  CONSTRAINT fk_eval_modulo FOREIGN KEY (id_modulo) REFERENCES modulos(id_modulo) ON DELETE CASCADE
);

CREATE TABLE preguntas_evaluacion (
  id_pregunta    INTEGER PRIMARY KEY AUTOINCREMENT,
  id_evaluacion  INTEGER NOT NULL,
  enunciado      TEXT NOT NULL,
  puntos         NUMERIC NOT NULL DEFAULT 1,
  CONSTRAINT fk_preg_eval FOREIGN KEY (id_evaluacion) REFERENCES evaluaciones(id_evaluacion) ON DELETE CASCADE
);

CREATE TABLE opciones_respuesta (
  id_opcion    INTEGER PRIMARY KEY AUTOINCREMENT,
  id_pregunta  INTEGER NOT NULL,
  texto        TEXT NOT NULL,
  es_correcta INTEGER NOT NULL DEFAULT 0 CHECK (es_correcta IN (0,1)),
  CONSTRAINT fk_opc_preg FOREIGN KEY (id_pregunta) REFERENCES preguntas_evaluacion(id_pregunta) ON DELETE CASCADE
);

CREATE TABLE intentos_evaluacion (
  id_intento      INTEGER PRIMARY KEY AUTOINCREMENT,
  id_inscripcion  INTEGER NOT NULL,
  id_evaluacion   INTEGER NOT NULL,
  calificacion    NUMERIC NOT NULL,
  aprobado INTEGER NOT NULL DEFAULT 0 CHECK (aprobado IN (0,1)),
  fecha_intento   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_int_insc FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion) ON DELETE CASCADE,
  CONSTRAINT fk_int_eval FOREIGN KEY (id_evaluacion)  REFERENCES evaluaciones(id_evaluacion)
);

CREATE TABLE pagos (
  id_pago         INTEGER PRIMARY KEY AUTOINCREMENT,
  id_inscripcion  INTEGER NOT NULL,
  monto           NUMERIC NOT NULL,
  metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('tarjeta','paypal','transferencia','oxxo','gratuito')),
  estatus TEXT NOT NULL DEFAULT 'pendiente' CHECK (estatus IN ('pendiente','aprobado','rechazado','reembolsado')),
  fecha_pago      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pago_insc FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion)
);

CREATE TABLE certificados (
  id_certificado  INTEGER PRIMARY KEY AUTOINCREMENT,
  id_inscripcion  INTEGER NOT NULL UNIQUE,
  codigo          TEXT NOT NULL UNIQUE,
  fecha_emision   TEXT NOT NULL,
  CONSTRAINT fk_cert_insc FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion)
);

CREATE TABLE resenas_curso (
  id_resena       INTEGER PRIMARY KEY AUTOINCREMENT,
  id_inscripcion  INTEGER NOT NULL UNIQUE,
  puntuacion      INTEGER NOT NULL CHECK (puntuacion BETWEEN 1 AND 5),
  comentario      TEXT NULL,
  fecha_resena    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_resena_insc FOREIGN KEY (id_inscripcion) REFERENCES inscripciones(id_inscripcion) ON DELETE CASCADE
);

CREATE INDEX idx_cursos_categoria ON cursos(id_categoria);
CREATE INDEX idx_cursos_instructor ON cursos(id_instructor);
CREATE INDEX idx_insc_curso ON inscripciones(id_curso);
