import pandas as pd
import streamlit as st
from conexion import BASES, crear_todas, get_connection

st.set_page_config(
    page_title="Proyecto Final | CRUD y Predicciones",
    page_icon="📊",
    layout="wide",
)

# Asegura que los 4 archivos .db existan desde el inicio
crear_todas()

st.title("📊 Sistema Integral de Gestión (CRUD) y Analítica Predictiva")
st.markdown(
    "**Alumno:** Eric Alberto Jimenez Garcia | **Grupo:** 71371  \n"
    "Selecciona cualquiera de las 4 bases de datos relacionales en el **menú lateral izquierdo** "
    "para operar su módulo CRUD y ejecutar simulaciones con Machine Learning."
)

st.divider()
st.subheader("Estado de las Bases de Datos SQLite")

cols = st.columns(4)

resumen_bases = [
    ("captacion_clientes", "1. Captación de Clientes", "prospectos", cols[0]),
    ("mercado_libre", "2. Mercado Libre", "publicaciones", cols[1]),
    ("elearning_cursos", "3. E-Learning Cursos", "cursos", cols[2]),
    ("ventas_nivel_republica", "4. Ventas República", "ventas", cols[3]),
]

for db_key, titulo, tabla_principal, col in resumen_bases:
    con = get_connection(db_key)
    total_tablas = pd.read_sql(
        "SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        con,
    )["n"][0]
    total_registros = pd.read_sql(f"SELECT COUNT(*) AS n FROM {tabla_principal}", con)["n"][0]
    con.close()

    with col:
        with st.container(border=True):
            st.markdown(f"### {titulo}")
            st.metric("Tablas relacionales", total_tablas)
            st.metric(f"Registros en `{tabla_principal}`", total_registros)

