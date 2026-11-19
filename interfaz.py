from collections.abc import Sequence

import streamlit as st


def render_sidebar(modulo: str, descripcion: str) -> None:
    with st.sidebar:
        with st.container(border=True):
            st.markdown("#### 📊 Analítica Predictiva")
            st.caption("Gestión de datos y modelos en un solo lugar.")

        st.markdown("**Módulo actual**")
        st.markdown(f"### {modulo}")
        st.caption(descripcion)


def render_page_header(titulo: str, descripcion: str) -> None:
    st.title(titulo)
    st.caption(descripcion)
    st.divider()


def render_kpi_cards(indicadores: Sequence[tuple[str, str | int | float]]) -> None:
    for columna, (etiqueta, valor) in zip(st.columns(len(indicadores)), indicadores):
        with columna:
            with st.container(border=True):
                st.metric(etiqueta, valor)
