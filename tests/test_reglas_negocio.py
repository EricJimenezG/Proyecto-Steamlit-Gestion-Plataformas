import sqlite3
import unittest

from reglas_negocio import sincronizar_cliente


class SincronizarClienteTests(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(":memory:")
        self.con.execute(
            """CREATE TABLE clientes (
                   id_cliente INTEGER PRIMARY KEY,
                   id_prospecto INTEGER NOT NULL UNIQUE,
                   fecha_conversion TEXT NOT NULL,
                   tipo_cliente TEXT NOT NULL,
                   activo INTEGER NOT NULL DEFAULT 1
               )"""
        )
        self.cur = self.con.cursor()

    def tearDown(self):
        self.con.close()

    def test_crea_y_reactiva_cliente_al_convertir(self):
        sincronizar_cliente(self.cur, 17, "convertido", "Empresa")
        fecha_original = self.cur.execute(
            "SELECT fecha_conversion FROM clientes WHERE id_prospecto = 17"
        ).fetchone()[0]

        sincronizar_cliente(self.cur, 17, "descartado", "Empresa")
        self.assertEqual(self.cur.execute("SELECT activo FROM clientes").fetchone()[0], 0)

        sincronizar_cliente(self.cur, 17, "convertido", "")
        cliente = self.cur.execute(
            "SELECT fecha_conversion, tipo_cliente, activo FROM clientes WHERE id_prospecto = 17"
        ).fetchone()
        self.assertEqual(cliente, (fecha_original, "persona", 1))

    def test_no_crea_cliente_para_prospecto_no_convertido(self):
        sincronizar_cliente(self.cur, 23, "nuevo", None)
        self.assertEqual(self.cur.execute("SELECT COUNT(*) FROM clientes").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
