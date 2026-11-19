from collections.abc import Callable
import sqlite3

from conexion import get_connection
from reglas_negocio import sincronizar_cliente


def _aplicar_semilla(
    nombre_db: str,
    consulta_marcador: str,
    marcador: str,
    insertar: Callable[[sqlite3.Cursor], None],
) -> bool:
    con = get_connection(nombre_db)
    try:
        cur = con.cursor()
        if cur.execute(consulta_marcador, (marcador,)).fetchone():
            return False
        insertar(cur)
        con.commit()
        return True
    finally:
        con.close()


def _agregar_prospectos(cur: sqlite3.Cursor) -> None:
    canales = cur.execute(
        "SELECT id_canal, tipo FROM canales_captacion WHERE activo = 1 ORDER BY id_canal"
    ).fetchall()
    campanas = cur.execute("SELECT id_campana FROM campanas ORDER BY id_campana").fetchall()
    asesores = cur.execute(
        "SELECT id_empleado FROM empleados WHERE activo = 1 ORDER BY id_empleado"
    ).fetchall()
    if not canales:
        raise ValueError("No hay canales activos para crear los prospectos de demostración.")

    estados = ("convertido", "descartado", "interesado", "contactado", "negociacion", "nuevo")
    nombres = ("Andrea", "Daniel", "Mariana", "Diego", "Valeria", "Emilio", "Camila", "Mateo")
    prospectos = []
    for numero in range(1, 61):
        id_canal, tipo_canal = canales[(numero - 1) % len(canales)]
        id_asesor = asesores[(numero - 1) % len(asesores)][0] if asesores and numero % 4 else None
        id_campana = campanas[(numero - 1) % len(campanas)][0] if campanas and numero % 3 else None
        puntuacion = int(id_asesor is not None) + int(id_campana is not None)
        puntuacion += int(tipo_canal in ("referido", "presencial"))
        convertido = puntuacion >= 2 and numero % 3 != 0
        estatus = "convertido" if convertido else estados[numero % (len(estados) - 1) + 1]
        empresa = f"Empresa Demo {numero:03d}" if numero % 3 else None
        prospectos.append(
            (
                nombres[(numero - 1) % len(nombres)],
                f"Demo {numero:03d}",
                f"prospecto.demo.{numero:03d}@example.test",
                f"559{numero:07d}",
                empresa,
                id_canal,
                id_campana,
                id_asesor,
                estatus,
            )
        )

    for prospecto in prospectos:
        cur.execute(
            """INSERT INTO prospectos
               (nombre, apellidos, correo, telefono, empresa, id_canal, id_campana, id_empleado, estatus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            prospecto,
        )
        sincronizar_cliente(cur, cur.lastrowid, prospecto[-1], prospecto[4])


def _agregar_publicaciones(cur: sqlite3.Cursor) -> None:
    vendedores = cur.execute(
        """SELECT id_usuario FROM usuarios
           WHERE tipo_usuario IN ('vendedor', 'ambos') AND activo = 1 ORDER BY id_usuario"""
    ).fetchall()
    categorias = cur.execute("SELECT id_categoria FROM categorias ORDER BY id_categoria").fetchall()
    compradores = cur.execute(
        """SELECT u.id_usuario, d.id_direccion
           FROM usuarios u
           JOIN direcciones d ON d.id_usuario = u.id_usuario
           WHERE u.tipo_usuario IN ('comprador', 'ambos') AND u.activo = 1
           ORDER BY u.id_usuario, d.id_direccion"""
    ).fetchall()
    if not vendedores or not categorias or not compradores:
        raise ValueError("Faltan vendedores, categorías o direcciones para crear ventas de demostración.")

    condiciones = ("nuevo", "usado", "reacondicionado")
    tipos = ("gratuita", "clasica", "premium")
    comprador, direccion = compradores[0]
    for numero in range(1, 41):
        vendedor = vendedores[(numero - 1) % len(vendedores)][0]
        categoria = categorias[(numero - 1) % len(categorias)][0]
        precio = float(180 + (numero * 173) % 3200)
        cur.execute(
            """INSERT INTO publicaciones
               (id_vendedor, id_categoria, titulo, descripcion, precio, stock, condicion,
                tipo_publicacion, envio_gratis, estatus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'activa')""",
            (
                vendedor,
                categoria,
                f"Publicación Demo {numero:03d}",
                "Artículo sintético para probar el análisis de demanda.",
                precio,
                40 + numero,
                condiciones[(numero - 1) % len(condiciones)],
                tipos[(numero - 1) % len(tipos)],
                int(numero % 2 == 0),
            ),
        )
        id_publicacion = cur.lastrowid
        if numero % 5 == 0:
            continue

        cantidad = 1 + (numero * 7) % 18
        total = precio * cantidad
        cur.execute(
            """INSERT INTO pedidos (id_comprador, id_direccion_envio, estatus, total)
               VALUES (?, ?, 'entregado', ?)""",
            (comprador, direccion, total),
        )
        id_pedido = cur.lastrowid
        cur.execute(
            """INSERT INTO detalle_pedido (id_pedido, id_publicacion, cantidad, precio_unitario)
               VALUES (?, ?, ?, ?)""",
            (id_pedido, id_publicacion, cantidad, precio),
        )


def _agregar_cursos(cur: sqlite3.Cursor) -> None:
    categorias = cur.execute("SELECT id_categoria FROM categorias_curso ORDER BY id_categoria").fetchall()
    instructores = cur.execute(
        "SELECT id_usuario FROM usuarios WHERE rol = 'instructor' AND activo = 1 ORDER BY id_usuario"
    ).fetchall()
    if not categorias or not instructores:
        raise ValueError("Faltan categorías o instructores activos para crear cursos de demostración.")

    estudiantes = []
    for numero in range(1, 31):
        cur.execute(
            """INSERT INTO usuarios
               (nombre, apellidos, correo, contrasena_hash, rol, activo)
               VALUES (?, ?, ?, ?, 'estudiante', 1)""",
            (
                f"Estudiante Demo {numero:03d}",
                "Práctica",
                f"estudiante.demo.{numero:03d}@example.test",
                "demo-no-utilizable-como-contrasena",
            ),
        )
        estudiantes.append(cur.lastrowid)

    for numero in range(1, 13):
        categoria = categorias[(numero - 1) % len(categorias)][0]
        instructor = instructores[(numero - 1) % len(instructores)][0]
        cur.execute(
            """INSERT INTO cursos
               (titulo, descripcion, id_categoria, id_instructor, nivel, precio, duracion_horas, estatus)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'publicado')""",
            (
                f"Curso Demo {numero:03d}",
                "Curso sintético para ampliar el conjunto de práctica.",
                categoria,
                instructor,
                ("basico", "intermedio", "avanzado")[(numero - 1) % 3],
                float((numero * 125) % 900),
                float(4 + (numero * 3) % 40),
            ),
        )

    cursos = [row[0] for row in cur.execute("SELECT id_curso FROM cursos ORDER BY id_curso").fetchall()]
    for indice_estudiante, estudiante in enumerate(estudiantes):
        for desplazamiento in range(4):
            curso = cursos[(indice_estudiante * 3 + desplazamiento) % len(cursos)]
            estado = (indice_estudiante + desplazamiento) % 4
            if estado == 0:
                progreso, estatus = float(5 + (indice_estudiante % 36)), "abandonada"
            elif estado == 1:
                progreso, estatus = float(30 + (indice_estudiante % 61)), "activa"
            else:
                progreso, estatus = 100.0, "completada"
            cur.execute(
                """INSERT INTO inscripciones (id_usuario, id_curso, progreso, estatus)
                   VALUES (?, ?, ?, ?)""",
                (estudiante, curso, progreso, estatus),
            )


def _agregar_ventas(cur: sqlite3.Cursor) -> None:
    sucursales_empleados = {}
    for id_sucursal, id_empleado in cur.execute(
        """SELECT id_sucursal, id_empleado FROM empleados
           WHERE activo = 1 ORDER BY id_empleado"""
    ).fetchall():
        sucursales_empleados.setdefault(id_sucursal, id_empleado)
    productos = cur.execute(
        """SELECT id_producto, precio_unitario FROM productos
           WHERE activo = 1 ORDER BY id_producto"""
    ).fetchall()
    if not sucursales_empleados or not productos:
        raise ValueError("Faltan empleados activos o productos para crear ventas de demostración.")

    sucursales = list(sucursales_empleados)
    metodos = ("efectivo", "tarjeta_credito", "tarjeta_debito", "transferencia")
    for numero in range(1, 61):
        id_sucursal = sucursales[(numero - 1) % len(sucursales)]
        id_empleado = sucursales_empleados[id_sucursal]
        id_producto, precio = productos[(numero * 3 - 1) % len(productos)]
        cantidad = 1 + (numero * 3) % 10
        subtotal = round(float(precio) * cantidad, 2)
        iva = round(subtotal * 0.16, 2)
        total = round(subtotal + iva, 2)
        anio = 2023 + (numero - 1) // 24
        mes = (numero - 1) % 12 + 1
        dia = (numero * 3 - 1) % 27 + 1
        cur.execute(
            """INSERT INTO ventas
               (folio, id_sucursal, id_empleado, fecha_venta, metodo_pago, subtotal, iva, total, estatus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completada')""",
            (
                f"DEMO-VTA-{numero:04d}",
                id_sucursal,
                id_empleado,
                f"{anio}-{mes:02d}-{dia:02d} 12:00:00",
                metodos[(numero - 1) % len(metodos)],
                subtotal,
                iva,
                total,
            ),
        )
        cur.execute(
            """INSERT INTO detalle_venta
               (id_venta, id_producto, cantidad, precio_unitario, descuento)
               VALUES (?, ?, ?, ?, 0)""",
            (cur.lastrowid, id_producto, cantidad, precio),
        )


def agregar_registros_demo(nombre_db: str) -> bool:
    semillas = {
        "captacion_clientes": (
            "SELECT 1 FROM prospectos WHERE correo = ?",
            "prospecto.demo.001@example.test",
            _agregar_prospectos,
        ),
        "mercado_libre": (
            "SELECT 1 FROM publicaciones WHERE titulo = ?",
            "Publicación Demo 001",
            _agregar_publicaciones,
        ),
        "elearning_cursos": (
            "SELECT 1 FROM usuarios WHERE correo = ?",
            "estudiante.demo.001@example.test",
            _agregar_cursos,
        ),
        "ventas_nivel_republica": (
            "SELECT 1 FROM ventas WHERE folio = ?",
            "DEMO-VTA-0001",
            _agregar_ventas,
        ),
    }
    if nombre_db not in semillas:
        raise ValueError(f"Base desconocida para datos demo: {nombre_db}")
    consulta, marcador, insertar = semillas[nombre_db]
    return _aplicar_semilla(nombre_db, consulta, marcador, insertar)
