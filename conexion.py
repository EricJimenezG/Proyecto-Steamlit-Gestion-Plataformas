"""
Practica de bases de datos y predicciones con Streamlit, SQLite.
Eric Alberto Jimenez Garcia
Grupo: 71371

Conexión a las 4 bases SQLite para usar en Streamlit.

Uso en app.py:
    import streamlit as st, pandas as pd
    from db import get_connection

    con = get_connection("mercado_libre")
    df = pd.read_sql("SELECT * FROM usuarios", con)
    st.dataframe(df)
"""
import sqlite3
from pathlib import Path

CARPETA = Path(__file__).parent

BASES = {
    "captacion_clientes":     "01_captacion_clientes.sql",
    "mercado_libre":          "02_mercado_libre.sql",
    "elearning_cursos":       "03_elearning_cursos.sql",
    "ventas_nivel_republica": "04_ventas_nivel_republica.sql",
}


def get_connection(nombre: str) -> sqlite3.Connection:
    """Abre la base (la crea desde su .sql si el .db no existe)."""
    if nombre not in BASES:
        raise ValueError(f"Base desconocida: {nombre}. Opciones: {list(BASES)}")
    ruta = CARPETA / f"{nombre}.db"
    nueva = not ruta.exists()
    con = sqlite3.connect(ruta, check_same_thread=False)  # necesario con Streamlit
    con.execute("PRAGMA foreign_keys = ON;")               # activar llaves foráneas
    con.row_factory = sqlite3.Row
    if nueva:
        con.executescript((CARPETA / BASES[nombre]).read_text(encoding="utf-8"))
        con.commit()
    return con


def crear_todas():
    """Crea los 4 archivos .db si no existen."""
    for nombre in BASES:
        get_connection(nombre).close()


if __name__ == "__main__":
    crear_todas()
    print("Bases listas:", ", ".join(BASES))
    