import sqlite3


def sincronizar_cliente(cur: sqlite3.Cursor, id_prospecto: int, estatus: str, empresa: str | None) -> None:
    if estatus == "convertido":
        tipo_cliente = "empresa" if empresa and empresa.strip() else "persona"
        cur.execute(
            """INSERT INTO clientes (id_prospecto, fecha_conversion, tipo_cliente)
               VALUES (?, date('now'), ?)
               ON CONFLICT(id_prospecto) DO UPDATE
               SET tipo_cliente = excluded.tipo_cliente, activo = 1""",
            (id_prospecto, tipo_cliente),
        )
    else:
        cur.execute("UPDATE clientes SET activo = 0 WHERE id_prospecto = ?", (id_prospecto,))
