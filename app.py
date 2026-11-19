from pathlib import Path
import pandas as pd
import streamlit as st
from conexion import BASES, crear_todas, get_connection
from interfaz import render_kpi_cards, render_page_header, render_sidebar

st.set_page_config(
    page_title="Proyecto Final | Predicciones",
    page_icon="📊",
    layout="wide",
)

crear_todas()

render_sidebar("Inicio", "Consulta el estado de las cuatro bases de datos.")

with st.sidebar:
    st.divider()
    with st.expander("⚙️ Administración de bases de datos"):
        st.caption("Restaura los archivos `.db` a sus datos iniciales. Se perderán los cambios realizados durante las pruebas.")
        if st.button("🔄 Restaurar bases de datos", width="stretch"):
            carpeta = Path(__file__).parent
            for nombre_db in BASES:
                archivo_db = carpeta / f"{nombre_db}.db"
                if archivo_db.exists():
                    archivo_db.unlink()
            crear_todas()
            st.cache_data.clear()
            st.success("Bases restauradas. Entra a cada módulo para regenerar sus datos demo.")
            st.rerun()

render_page_header(
    "📊 Centro de analítica",
    "Administra y explora los datos de tus módulos de predicción.",
)
st.caption("Alumno: Eric Alberto Jimenez Garcia · Grupo: 71371")

resumen_bases = [
    (
        "captacion_clientes",
        "🎯 Captación de Clientes",
        "prospectos",
        "Seguimiento del embudo comercial y estimación de conversiones.",
        "pages/captacion_clientes.py",
    ),
    (
        "mercado_libre",
        "🛒 Mercado Libre",
        "publicaciones",
        "Gestión del catálogo y análisis de demanda de productos.",
        "pages/mercado_libre.py",
    ),
    (
        "elearning_cursos",
        "🎓 E-Learning",
        "cursos",
        "Administración de cursos e indicadores de permanencia.",
        "pages/elearning_cursos.py",
    ),
    (
        "ventas_nivel_republica",
        "🇲🇽 Ventas República",
        "ventas",
        "Resumen comercial y proyección de ingresos.",
        "pages/ventas_republica.py",
    ),
]

resumenes = []
for db_key, titulo, tabla_principal, descripcion, pagina in resumen_bases:
    con = get_connection(db_key)
    total_tablas = pd.read_sql(
        "SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        con,
    )["n"][0]
    total_registros = pd.read_sql(f"SELECT COUNT(*) AS n FROM {tabla_principal}", con)["n"][0]
    con.close()
    resumenes.append((titulo, tabla_principal, total_tablas, total_registros, descripcion, pagina))

st.subheader("Vista general")
render_kpi_cards(
    [
        ("Módulos", len(resumenes)),
        ("Tablas relacionales", sum(resumen[2] for resumen in resumenes)),
        ("Registros", f"{sum(resumen[3] for resumen in resumenes):,}"),
    ]
)

st.subheader("Explora tus módulos")
for inicio in range(0, len(resumenes), 2):
    columnas = st.columns(2)
    for columna, resumen in zip(columnas, resumenes[inicio : inicio + 2]):
        titulo, tabla, total_tablas, total_registros, descripcion, pagina = resumen
        with columna:
            with st.container(border=True):
                st.markdown(f"### {titulo}")
                st.caption(descripcion)
                metricas = st.columns(2)
                metricas[0].metric("Tablas", total_tablas)
                metricas[1].metric(f"Registros en {tabla}", total_registros)
                st.page_link(
                    pagina,
                    label="Abrir módulo",
                    icon=":material/arrow_forward:",
                    width="stretch",
                )