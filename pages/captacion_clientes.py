import sqlite3
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection

st.set_page_config(page_title="Captación de Clientes", page_icon="🎯", layout="wide")


def inicializar_datos_demo():
    con = get_connection("captacion_clientes")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM canales_captacion")
    if cur.fetchone()[0] > 0:
        con.close()
        return

    canales = [
        ("Facebook Ads", "digital"),
        ("Google Search", "digital"),
        ("Expo Universitaria", "presencial"),
        ("Recomendación Directa", "referido"),
        ("Llamada en Frío", "telefonico"),
    ]
    cur.executemany("INSERT INTO canales_captacion (nombre, tipo) VALUES (?, ?)", canales)

    campanas = [
        ("Campaña Otoño 2026", 1, "2026-09-01", "2026-11-30", 15000.0, "Captación digital"),
        ("Feria Tecnológica", 3, "2026-10-10", "2026-10-15", 8000.0, "Leads B2B"),
    ]
    cur.executemany(
        "INSERT INTO campanas (nombre, id_canal, fecha_inicio, fecha_fin, presupuesto, objetivo) VALUES (?, ?, ?, ?, ?, ?)",
        campanas,
    )

    empleados = [
        ("Marcos", "Ruiz", "m.ruiz@empresa.mx", "5512345678", "Ejecutivo Sr"),
        ("Elena", "Paredes", "e.paredes@empresa.mx", "5587654321", "Ejecutivo Jr"),
    ]
    cur.executemany(
        "INSERT INTO empleados (nombre, apellidos, correo, telefono, puesto) VALUES (?, ?, ?, ?, ?)",
        empleados,
    )

    prospectos = [
        ("Roberto", "Díaz", "roberto@mail.com", "5511112222", "TechSA", 3, 2, 1, "convertido"),
        ("María", "López", "maria@mail.com", "5522223333", "Innovar", 4, None, 1, "convertido"),
        ("Fernanda", "Solís", "fer@mail.com", "5533334444", "Comercial MX", 3, 2, 2, "convertido"),
        ("Andrés", "Nava", "andres@mail.com", "5544445555", "Logística Pro", 4, None, 1, "convertido"),
        ("Patricia", "Vega", "paty@mail.com", "5555556666", "Grupo Alfa", 1, 1, 2, "descartado"),
        ("Héctor", "Mora", "hector@mail.com", "5566667777", "Servicios IT", 5, None, 2, "descartado"),
        ("Lucía", "Reyes", "lucia@mail.com", "5577778888", "Retail Plus", 2, 1, 1, "contactado"),
        ("Óscar", "Campos", "oscar@mail.com", "5588889999", "Constructora Z", 5, None, 2, "nuevo"),
        ("Daniela", "Ortiz", "dani@mail.com", "5599990000", "Consultores", 1, 1, 1, "negociacion"),
        ("Raúl", "Méndez", "raul@mail.com", "5500001111", "Industrias K", 4, None, 1, "convertido"),
    ]
    cur.executemany(
        """INSERT INTO prospectos 
           (nombre, apellidos, correo, telefono, empresa, id_canal, id_campana, id_empleado, estatus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        prospectos,
    )
    con.commit()
    con.close()


inicializar_datos_demo()

st.title("🎯 Captación de Clientes: CRUD y Predicción de Conversión")
tab_crud, tab_pred = st.tabs(["📋 CRUD de Prospectos", "🤖 Predicción de Cierre (ML)"])

# ---------------------------------------------------------------------
# PESTAÑA 1: CRUD DE PROSPECTOS
# ---------------------------------------------------------------------
with tab_crud:
    con = get_connection("captacion_clientes")
    df_canales = pd.read_sql("SELECT id_canal, nombre || ' (' || tipo || ')' AS canal FROM canales_captacion", con)
    df_empleados = pd.read_sql("SELECT id_empleado, nombre || ' ' || apellidos AS asesor FROM empleados", con)

    st.subheader("Listado de Prospectos")
    df_prospectos = pd.read_sql(
        """
        SELECT p.id_prospecto AS ID,
               p.nombre AS Nombre,
               p.apellidos AS Apellidos,
               p.empresa AS Empresa,
               c.nombre AS Canal,
               c.tipo AS Tipo_Canal,
               COALESCE(e.nombre || ' ' || e.apellidos, 'Sin asignar') AS Asesor,
               p.estatus AS Estatus
        FROM prospectos p
        JOIN canales_captacion c ON p.id_canal = c.id_canal
        LEFT JOIN empleados e ON p.id_empleado = e.id_empleado
        ORDER BY p.id_prospecto DESC
        """,
        con,
    )
    st.dataframe(df_prospectos, use_container_width=True, hide_index=True)

    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("➕ Registrar Prospecto")
        with st.form("crear_prospecto", clear_on_submit=True):
            nombre = st.text_input("Nombre*")
            apellidos = st.text_input("Apellidos*")
            empresa = st.text_input("Empresa")
            canal_sel = st.selectbox("Canal de captación", df_canales["canal"])
            asesor_sel = st.selectbox("Asesor asignado", df_empleados["asesor"])
            estatus = st.selectbox(
                "Estatus inicial",
                ["nuevo", "contactado", "interesado", "negociacion", "convertido", "descartado"],
            )

            if st.form_submit_button("Guardar Prospecto", use_container_width=True):
                if not nombre.strip() or not apellidos.strip():
                    st.error("Nombre y apellidos son obligatorios.")
                else:
                    id_canal = int(df_canales.loc[df_canales["canal"] == canal_sel, "id_canal"].values[0])
                    id_emp = int(df_empleados.loc[df_empleados["asesor"] == asesor_sel, "id_empleado"].values[0])
                    cur = con.cursor()
                    cur.execute(
                        """INSERT INTO prospectos (nombre, apellidos, empresa, id_canal, id_empleado, estatus)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (nombre.strip(), apellidos.strip(), empresa.strip(), id_canal, id_emp, estatus),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Prospecto registrado.")
                    st.rerun()

    with c2:
        st.subheader("✏️ Actualizar Estatus")
        if not df_prospectos.empty:
            opciones = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_prospectos.iterrows()}
            sel = st.selectbox("Seleccionar prospecto", list(opciones.keys()))
            id_edit = opciones[sel]
            actual = df_prospectos[df_prospectos["ID"] == id_edit].iloc[0]

            with st.form("editar_prospecto"):
                nueva_emp = st.text_input("Empresa", value=actual["Empresa"] or "")
                estados = ["nuevo", "contactado", "interesado", "negociacion", "convertido", "descartado"]
                nuevo_est = st.selectbox("Estatus", estados, index=estados.index(actual["Estatus"]))

                if st.form_submit_button("Actualizar", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        "UPDATE prospectos SET empresa = ?, estatus = ? WHERE id_prospecto = ?",
                        (nueva_emp.strip(), nuevo_est, id_edit),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Datos actualizados.")
                    st.rerun()

    with c3:
        st.subheader("🗑️ Eliminar Prospecto")
        if not df_prospectos.empty:
            opciones_del = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_prospectos.iterrows()}
            sel_del = st.selectbox("Prospecto a eliminar", list(opciones_del.keys()))
            id_del = opciones_del[sel_del]

            if st.button("Eliminar Registro", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM prospectos WHERE id_prospecto = ?", (id_del,))
                    con.commit()
                    st.cache_data.clear()
                    st.success("Prospecto eliminado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: este prospecto ya está vinculado en la tabla `clientes`.")

    con.close()

# ---------------------------------------------------------------------
# PESTAÑA 2: MODELO PREDICTIVO CORREGIDO
# ---------------------------------------------------------------------
with tab_pred:
    st.subheader("Simulador de Probabilidad de Conversión")

    @st.cache_data
    def cargar_datos_entrenamiento():
        con = get_connection("captacion_clientes")
        query = """
            SELECT p.estatus, c.tipo AS tipo_canal, COALESCE(p.id_empleado, 0) AS tiene_asesor
            FROM prospectos p
            JOIN canales_captacion c ON p.id_canal = c.id_canal
        """
        df = pd.read_sql(query, con)
        con.close()  # Corrección 1: cierre explícito de conexión

        if df.empty or df["estatus"].eq("convertido").nunique() < 2:
            return pd.DataFrame(), pd.Series(), None

        df["convertido"] = (df["estatus"] == "convertido").astype(int)
        df["tiene_asesor"] = (df["tiene_asesor"] > 0).astype(int)

        le = LabelEncoder()
        df["tipo_canal_encoded"] = le.fit_transform(df["tipo_canal"])

        X = df[["tipo_canal_encoded", "tiene_asesor"]]
        y = df["convertido"]
        return X, y, le

    X, y, encoder = cargar_datos_entrenamiento()

    if encoder is None or len(X) < 4:
        st.warning("Se requieren al menos 4 prospectos con estatus variados (convertidos y no convertidos) para entrenar.")
    else:
        modelo = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        modelo.fit(X, y)

        col_in, col_out = st.columns(2)
        with col_in:
            canal_seleccionado = st.selectbox("Tipo de canal de captación:", encoder.classes_)
            asignar_asesor = st.checkbox("¿Tiene asesor comercial asignado?", value=True)
            btn_pred = st.button("Predecir Probabilidad de Conversión", type="primary")

        with col_out:
            if btn_pred:
                input_encoded = encoder.transform([canal_seleccionado])[0]
                # Corrección 3: pasar DataFrame con los mismos nombres de columnas que X
                X_nuevo = pd.DataFrame(
                    [[input_encoded, int(asignar_asesor)]],
                    columns=["tipo_canal_encoded", "tiene_asesor"],
                )
                # Corrección 2: verificar que la clase 1 exista en modelo.classes_
                idx_clase_1 = list(modelo.classes_).index(1)
                probabilidad = modelo.predict_proba(X_nuevo)[0][idx_clase_1]

                st.metric("Probabilidad de Conversión", f"{probabilidad * 100:.1f}%")
                if probabilidad >= 0.5:
                    st.success("✅ Alta probabilidad de cierre.")
                else:
                    st.error("⚠️ Probabilidad baja. Se recomienda seguimiento presencial o referido.")