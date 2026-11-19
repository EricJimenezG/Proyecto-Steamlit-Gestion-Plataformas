import streamlit as st


def render_sidebar(modulo: str, descripcion: str) -> None:
    with st.sidebar:
        with st.container(border=True):
            st.markdown("#### 📊 Analítica Predictiva")
            st.caption("Gestión de datos y modelos en un solo lugar.")

        st.markdown("**Módulo actual**")
        st.markdown(f"### {modulo}")
        st.caption(descripcion)
