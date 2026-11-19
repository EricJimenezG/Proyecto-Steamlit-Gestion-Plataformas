import sqlite3
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection

st.set_page_config(page_title="Captación de Clientes | CRUD & ML", page_icon="🎯", layout="wide")


# =====================================================================
# 1. POBLADO INICIAL DE DATOS CON VARIANZA PARA ENTRENAMIENTO
# =====================================================================
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
        ("Marcos", "Ruiz", "m.ruiz@empresa.mx", "5512345678", "Ejecutivo Sr", 1),
        ("Elena", "Paredes", "e.paredes@empresa.mx", "5587654321", "Ejecutivo Jr", 1),
        ("Javier", "Montoya", "j.montoya@empresa.mx", "5544332211", "Consultor B2B", 1),
    ]
    cur.executemany(
        "INSERT INTO empleados (nombre, apellidos, correo, telefono, puesto, activo) VALUES (?, ?, ?, ?, ?, ?)",
        empleados,
    )

    # Datos con varianza real en asesor (id_empleado) y campaña (id_campana)
    prospectos = [
        ("Roberto", "Díaz", "roberto@mail.com", "5511112222", "TechSA", 3, 2, 1, "convertido"),
        ("María", "López", "maria@mail.com", "5522223333", "Innovar", 4, None, 1, "convertido"),
        ("Fernanda", "Solís", "fer@mail.com", "5533334444", "Comercial MX", 3, 2, 2, "convertido"),
        ("Andrés", "Nava", "andres@mail.com", "5544445555", "Logística Pro", 4, None, 3, "convertido"),
        ("Raúl", "Méndez", "raul@mail.com", "5500001111", "Industrias K", 4, 2, 1, "convertido"),
        ("Patricia", "Vega", "paty@mail.com", "5555556666", "Grupo Alfa", 1, 1, None, "descartado"),
        ("Héctor", "Mora", "hector@mail.com", "5566667777", "Servicios IT", 5, None, None, "descartado"),
        ("Lucía", "Reyes", "lucia@mail.com", "5577778888", "Retail Plus", 2, 1, 2, "contactado"),
        ("Óscar", "Campos", "oscar@mail.com", "5588889999", "Constructora Z", 5, None, None, "nuevo"),
        ("Daniela", "Ortiz", "dani@mail.com", "5599990000", "Consultores", 1, 1, 3, "negociacion"),
        ("Karla", "Pineda", "karla@mail.com", "5512123434", "Textiles Norte", 2, None, None, "descartado"),
        ("Mateo", "Salgado", "mateo@mail.com", "5598987676", "Distribuidora Sur", 1, 1, 1, "convertido"),
    ]
    cur.executemany(
        """INSERT INTO prospectos 
           (nombre, apellidos, correo, telefono, empresa, id_canal, id_campana, id_empleado, estatus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        prospectos,
    )

    # Registrar automáticamente en `clientes` a los prospectos que ya nacen como 'convertido'
    cur.execute(
        """INSERT INTO clientes (id_prospecto, fecha_conversion, tipo_cliente)
           SELECT id_prospecto, date('now'), CASE WHEN empresa IS NOT NULL AND empresa != '' THEN 'empresa' ELSE 'persona' END
           FROM prospectos WHERE estatus = 'convertido'"""
    )

    con.commit()
    con.close()


def registrar_cliente_si_convertido(cur: sqlite3.Cursor, id_prospecto: int, empresa: str):
    """Inserta en `clientes` si el prospecto alcanza el estatus 'convertido'."""
    tipo = "empresa" if empresa and empresa.strip() else "persona"
    cur.execute(
        """INSERT OR IGNORE INTO clientes (id_prospecto, fecha_conversion, tipo_cliente)
           VALUES (?, date('now'), ?)""",
        (id_prospecto, tipo),
    )


inicializar_datos_demo()

st.title("🎯 Captación de Clientes: Gestión Integral y Analítica Predictiva")

tab_prospectos, tab_asesores, tab_pred = st.tabs(
    ["📋 CRUD de Prospectos", "👔 CRUD de Asesores", "🤖 Predicción de Cierre (ML)"]
)

# =====================================================================
# PESTAÑA 1: CRUD DE PROSPECTOS + KPIs + GRÁFICAS + EXPORTACIÓN CSV
# =====================================================================
with tab_prospectos:
    con = get_connection("captacion_clientes")

    df_canales = pd.read_sql(
        "SELECT id_canal, nombre || ' (' || tipo || ')' AS canal FROM canales_captacion WHERE activo = 1", con
    )
    df_campanas = pd.read_sql("SELECT id_campana, nombre FROM campanas", con)
    df_empleados = pd.read_sql(
        "SELECT id_empleado, nombre || ' ' || apellidos AS asesor FROM empleados WHERE activo = 1", con
    )

    df_prospectos = pd.read_sql(
        """
        SELECT p.id_prospecto AS ID,
               p.nombre AS Nombre,
               p.apellidos AS Apellidos,
               p.empresa AS Empresa,
               c.nombre AS Canal,
               c.tipo AS Tipo_Canal,
               COALESCE(cam.nombre, 'Orgánico / Sin campaña') AS Campaña,
               COALESCE(e.nombre || ' ' || e.apellidos, 'Sin asignar') AS Asesor,
               p.estatus AS Estatus,
               CASE WHEN cl.id_cliente IS NOT NULL THEN 'Sí (ID ' || cl.id_cliente || ')' ELSE 'No' END AS Cliente_Registrado
        FROM prospectos p
        JOIN canales_captacion c ON p.id_canal = c.id_canal
        LEFT JOIN campanas cam ON p.id_campana = cam.id_campana
        LEFT JOIN empleados e ON p.id_empleado = e.id_empleado
        LEFT JOIN clientes cl ON p.id_prospecto = cl.id_prospecto
        ORDER BY p.id_prospecto DESC
        """,
        con,
    )

    # --- KPIs Ejecutivos ---
    total_prosp = len(df_prospectos)
    total_conv = int((df_prospectos["Estatus"] == "convertido").sum()) if total_prosp > 0 else 0
    tasa_conv = (total_conv / total_prosp * 100) if total_prosp > 0 else 0.0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total de Prospectos", total_prosp)
    k2.metric("Clientes Convertidos", total_conv)
    k3.metric("Tasa de Conversión", f"{tasa_conv:.1f}%")

    # --- Gráficas de Embudo y Canales ---
    if not df_prospectos.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Distribución por Estatus del Embudo")
            st.bar_chart(df_prospectos["Estatus"].value_counts(), height=220)
        with g2:
            st.caption("Prospectos por Canal de Captación")
            st.bar_chart(df_prospectos["Canal"].value_counts(), height=220)

    # --- Tabla Principal (READ) + Descarga CSV ---
    st.subheader("Listado General de Prospectos")
    st.dataframe(df_prospectos, use_container_width=True, hide_index=True)

    csv_data = df_prospectos.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Exportar Prospectos a CSV",
        data=csv_data,
        file_name="reporte_prospectos.csv",
        mime="text/csv",
    )

    st.divider()
    c1, c2, c3 = st.columns(3)

    # --- CREATE PROSPECTO ---
    with c1:
        st.subheader("➕ Registrar Prospecto")
        with st.form("crear_prospecto", clear_on_submit=True):
            nombre = st.text_input("Nombre*")
            apellidos = st.text_input("Apellidos*")
            empresa = st.text_input("Empresa")
            canal_sel = st.selectbox("Canal de captación", df_canales["canal"])

            opciones_campana = ["Sin campaña"] + df_campanas["nombre"].tolist()
            campana_sel = st.selectbox("Campaña asociada", opciones_campana)

            opciones_asesor = ["Sin asignar"] + df_empleados["asesor"].tolist()
            asesor_sel = st.selectbox("Asesor asignado", opciones_asesor)

            estatus = st.selectbox(
                "Estatus inicial",
                ["nuevo", "contactado", "interesado", "negociacion", "convertido", "descartado"],
            )

            if st.form_submit_button("Guardar Prospecto", use_container_width=True):
                if not nombre.strip() or not apellidos.strip():
                    st.error("Nombre y apellidos son obligatorios.")
                else:
                    id_canal = int(df_canales.loc[df_canales["canal"] == canal_sel, "id_canal"].values[0])
                    id_campana = (
                        None
                        if campana_sel == "Sin campaña"
                        else int(df_campanas.loc[df_campanas["nombre"] == campana_sel, "id_campana"].values[0])
                    )
                    id_emp = (
                        None
                        if asesor_sel == "Sin asignar"
                        else int(df_empleados.loc[df_empleados["asesor"] == asesor_sel, "id_empleado"].values[0])
                    )

                    cur = con.cursor()
                    cur.execute(
                        """INSERT INTO prospectos (nombre, apellidos, empresa, id_canal, id_campana, id_empleado, estatus)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (nombre.strip(), apellidos.strip(), empresa.strip(), id_canal, id_campana, id_emp, estatus),
                    )
                    nuevo_id = cur.lastrowid
                    if estatus == "convertido":
                        registrar_cliente_si_convertido(cur, nuevo_id, empresa)

                    con.commit()
                    st.cache_data.clear()
                    st.success("Prospecto registrado correctamente.")
                    st.rerun()

    # --- UPDATE PROSPECTO ---
    with c2:
        st.subheader("✏️ Actualizar Prospecto")
        if not df_prospectos.empty:
            opciones = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_prospectos.iterrows()}
            sel = st.selectbox("Seleccionar prospecto", list(opciones.keys()))
            id_edit = opciones[sel]
            actual = df_prospectos[df_prospectos["ID"] == id_edit].iloc[0]

            with st.form("editar_prospecto"):
                nueva_emp = st.text_input("Empresa", value=actual["Empresa"] or "")

                lista_asesores = ["Sin asignar"] + df_empleados["asesor"].tolist()
                idx_asesor = lista_asesores.index(actual["Asesor"]) if actual["Asesor"] in lista_asesores else 0
                nuevo_asesor_sel = st.selectbox("Reasignar asesor", lista_asesores, index=idx_asesor)

                estados = ["nuevo", "contactado", "interesado", "negociacion", "convertido", "descartado"]
                nuevo_est = st.selectbox("Estatus", estados, index=estados.index(actual["Estatus"]))

                if st.form_submit_button("Actualizar Datos", use_container_width=True):
                    nuevo_id_emp = (
                        None
                        if nuevo_asesor_sel == "Sin asignar"
                        else int(df_empleados.loc[df_empleados["asesor"] == nuevo_asesor_sel, "id_empleado"].values[0])
                    )
                    cur = con.cursor()
                    cur.execute(
                        "UPDATE prospectos SET empresa = ?, id_empleado = ?, estatus = ? WHERE id_prospecto = ?",
                        (nueva_emp.strip(), nuevo_id_emp, nuevo_est, id_edit),
                    )
                    if nuevo_est == "convertido":
                        registrar_cliente_si_convertido(cur, id_edit, nueva_emp)

                    con.commit()
                    st.cache_data.clear()
                    st.success("Prospecto actualizado (si pasó a 'convertido', se registró en `clientes`).")
                    st.rerun()

    # --- DELETE PROSPECTO ---
    with c3:
        st.subheader("🗑️ Eliminar Prospecto")
        if not df_prospectos.empty:
            opciones_del = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_prospectos.iterrows()}
            sel_del = st.selectbox("Prospecto a eliminar", list(opciones_del.keys()))
            id_del = opciones_del[sel_del]

            st.caption("Los prospectos ya convertidos en `clientes` están protegidos contra borrado accidental.")
            if st.button("Eliminar Prospecto", type="primary", use_container_width=True):
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


# =====================================================================
# PESTAÑA 2: CRUD DE ASESORES (TABLA `empleados`)
# =====================================================================
with tab_asesores:
    con = get_connection("captacion_clientes")

    st.subheader("Equipo Comercial (Asesores)")
    df_asesores = pd.read_sql(
        """
        SELECT e.id_empleado AS ID,
               e.nombre AS Nombre,
               e.apellidos AS Apellidos,
               e.correo AS Correo,
               COALESCE(e.telefono, '') AS Teléfono,
               e.puesto AS Puesto,
               CASE WHEN e.activo = 1 THEN 'Activo' ELSE 'Inactivo' END AS Estado,
               COUNT(p.id_prospecto) AS Prospectos_Asignados,
               SUM(CASE WHEN p.estatus = 'convertido' THEN 1 ELSE 0 END) AS Conversiones
        FROM empleados e
        LEFT JOIN prospectos p ON e.id_empleado = p.id_empleado
        GROUP BY e.id_empleado
        ORDER BY e.id_empleado ASC
        """,
        con,
    )
    st.dataframe(df_asesores, use_container_width=True, hide_index=True)

    st.divider()
    col_ac, col_au, col_ad = st.columns(3)

    # --- CREATE ASESOR ---
    with col_ac:
        st.subheader("➕ Nuevo Asesor")
        with st.form("form_crear_asesor", clear_on_submit=True):
            a_nombre = st.text_input("Nombre*")
            a_apellidos = st.text_input("Apellidos*")
            a_correo = st.text_input("Correo corporativo*")
            a_tel = st.text_input("Teléfono")
            a_puesto = st.selectbox("Puesto", ["Ejecutivo Jr", "Ejecutivo Sr", "Consultor B2B", "Gerente Comercial"])
            a_activo = st.checkbox("Activo", value=True)

            if st.form_submit_button("Registrar Asesor", use_container_width=True):
                if not a_nombre.strip() or not a_apellidos.strip() or not a_correo.strip():
                    st.error("Nombre, apellidos y correo son obligatorios.")
                else:
                    try:
                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO empleados (nombre, apellidos, correo, telefono, puesto, activo)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (a_nombre.strip(), a_apellidos.strip(), a_correo.strip(), a_tel.strip(), a_puesto, int(a_activo)),
                        )
                        con.commit()
                        st.success("Asesor registrado.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ese correo ya está registrado para otro asesor.")

    # --- UPDATE ASESOR ---
    with col_au:
        st.subheader("✏️ Editar Asesor")
        if not df_asesores.empty:
            opc_a = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_asesores.iterrows()}
            sel_a = st.selectbox("Selecciona asesor", list(opc_a.keys()))
            id_a_edit = opc_a[sel_a]
            asesor_act = df_asesores[df_asesores["ID"] == id_a_edit].iloc[0]

            with st.form("form_editar_asesor"):
                edit_tel = st.text_input("Teléfono", value=asesor_act["Teléfono"])
                puestos = ["Ejecutivo Jr", "Ejecutivo Sr", "Consultor B2B", "Gerente Comercial"]
                idx_p = puestos.index(asesor_act["Puesto"]) if asesor_act["Puesto"] in puestos else 0
                edit_puesto = st.selectbox("Puesto", puestos, index=idx_p)
                edit_activo = st.checkbox("Asesor activo", value=(asesor_act["Estado"] == "Activo"))

                if st.form_submit_button("Guardar Cambios", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        "UPDATE empleados SET telefono = ?, puesto = ?, activo = ? WHERE id_empleado = ?",
                        (edit_tel.strip(), edit_puesto, int(edit_activo), id_a_edit),
                    )
                    con.commit()
                    st.success("Datos del asesor actualizados.")
                    st.rerun()

    # --- DELETE ASESOR ---
    with col_ad:
        st.subheader("🗑️ Eliminar Asesor")
        if not df_asesores.empty:
            opc_adel = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_asesores.iterrows()}
            sel_adel = st.selectbox("Asesor a eliminar", list(opc_adel.keys()))
            id_a_del = opc_adel[sel_adel]

            st.caption("Al eliminar un asesor, sus prospectos quedan como 'Sin asignar' (`ON DELETE SET NULL`).")
            if st.button("Eliminar Asesor", type="primary", use_container_width=True):
                cur = con.cursor()
                cur.execute("DELETE FROM empleados WHERE id_empleado = ?", (id_a_del,))
                con.commit()
                st.cache_data.clear()
                st.success("Asesor eliminado.")
                st.rerun()

    con.close()


# =====================================================================
# PESTAÑA 3: MODELO PREDICTIVO CON EXPLICABILIDAD
# =====================================================================
with tab_pred:
    st.subheader("Simulador de Probabilidad de Conversión")
    st.write(
        "Entrena un clasificador **Random Forest** usando el historial de `prospectos`, `canales_captacion` "
        "y `campanas` para predecir el cierre comercial."
    )

    @st.cache_data
    def cargar_datos_entrenamiento():
        con = get_connection("captacion_clientes")
        query = """
            SELECT p.estatus,
                   c.tipo AS tipo_canal,
                   CASE WHEN p.id_empleado IS NOT NULL THEN 1 ELSE 0 END AS tiene_asesor,
                   CASE WHEN p.id_campana IS NOT NULL THEN 1 ELSE 0 END AS tiene_campana
            FROM prospectos p
            JOIN canales_captacion c ON p.id_canal = c.id_canal
        """
        df = pd.read_sql(query, con)
        con.close()

        if df.empty or df["estatus"].eq("convertido").nunique() < 2:
            return pd.DataFrame(), pd.Series(), None, pd.DataFrame()

        df["convertido"] = (df["estatus"] == "convertido").astype(int)

        le = LabelEncoder()
        df["tipo_canal_encoded"] = le.fit_transform(df["tipo_canal"])

        features = ["tipo_canal_encoded", "tiene_asesor", "tiene_campana"]
        X = df[features]
        y = df["convertido"]
        return X, y, le, df

    X, y, encoder, df_hist = cargar_datos_entrenamiento()

    if encoder is None or len(X) < 4:
        st.warning("Se requieren al menos 4 prospectos con estatus variados (convertidos y no convertidos) para entrenar.")
    else:
        modelo = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        modelo.fit(X, y)

        col_in, col_out = st.columns(2)
        with col_in:
            st.markdown("#### Parámetros del Prospecto")
            canal_seleccionado = st.selectbox("Tipo de canal de captación:", encoder.classes_)
            asignar_asesor = st.checkbox("¿Tiene asesor comercial asignado?", value=True)
            proviene_campana = st.checkbox("¿Proviene de una campaña activa?", value=True)
            btn_pred = st.button("Predecir Probabilidad de Conversión", type="primary", use_container_width=True)

        with col_out:
            st.markdown("#### Resultado de la Inferencia")
            if btn_pred:
                input_encoded = encoder.transform([canal_seleccionado])[0]
                X_nuevo = pd.DataFrame(
                    [[input_encoded, int(asignar_asesor), int(proviene_campana)]],
                    columns=["tipo_canal_encoded", "tiene_asesor", "tiene_campana"],
                )
                idx_clase_1 = list(modelo.classes_).index(1)
                probabilidad = modelo.predict_proba(X_nuevo)[0][idx_clase_1]

                st.metric("Probabilidad de Conversión", f"{probabilidad * 100:.1f}%")
                if probabilidad >= 0.5:
                    st.success("✅ Alta probabilidad de cierre comercial.")
                else:
                    st.error("⚠️ Probabilidad baja. Se sugiere asignar asesor o canal referido/presencial.")

        st.divider()
        exp1, exp2 = st.columns(2)

        with exp1:
            st.markdown("#### Importancia de Variables en el Modelo")
            df_imp = pd.DataFrame(
                {
                    "Variable": ["Tipo de Canal", "Asesor Asignado", "Origen de Campaña"],
                    "Importancia": modelo.feature_importances_,
                }
            ).set_index("Variable")
            st.bar_chart(df_imp, height=220)

        with exp2:
            st.markdown("#### Tasa Histórica Real por Tipo de Canal")
            resumen_canal = (
                df_hist.groupby("tipo_canal")["convertido"]
                .agg(Total="count", Convertidos="sum")
                .reset_index()
            )
            resumen_canal["Tasa_Cierre (%)"] = (resumen_canal["Convertidos"] / resumen_canal["Total"] * 100).round(1)
            st.dataframe(resumen_canal, use_container_width=True, hide_index=True)