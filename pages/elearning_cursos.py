import sqlite3
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection

st.set_page_config(page_title="E-Learning | CRUD & Predicciones", page_icon="🎓", layout="wide")


# =====================================================================
# 1. POBLADO INICIAL DE DATOS (Solo si la BD está vacía)
# =====================================================================
def inicializar_datos_demo():
    con = get_connection("elearning_cursos")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] > 0:
        con.close()
        return

    # 1. Usuarios (3 instructores, 6 estudiantes)
    usuarios = [
        ("Carlos", "Mendoza", "carlos.inst@edu.mx", "hash123", "instructor", "Especialista en Ciencia de Datos y Python", 1),
        ("Laura", "Gómez", "laura.inst@edu.mx", "hash123", "instructor", "Desarrolladora Full-Stack y Arquitecta Cloud", 1),
        ("Roberto", "Sánchez", "roberto.inst@edu.mx", "hash123", "instructor", "Ingeniero de Redes y Ciberseguridad", 1),
        ("Ana", "Torres", "ana@alumno.mx", "hash123", "estudiante", None, 1),
        ("Luis", "Ramírez", "luis@alumno.mx", "hash123", "estudiante", None, 1),
        ("Sofía", "Hernández", "sofia@alumno.mx", "hash123", "estudiante", None, 1),
        ("Diego", "Vargas", "diego@alumno.mx", "hash123", "estudiante", None, 1),
        ("Valeria", "Cruz", "valeria@alumno.mx", "hash123", "estudiante", None, 1),
        ("Jorge", "Silva", "jorge@alumno.mx", "hash123", "estudiante", None, 1),
    ]
    cur.executemany(
        """INSERT INTO usuarios (nombre, apellidos, correo, contrasena_hash, rol, biografia, activo) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        usuarios,
    )

    # 2. Categorías
    categorias = [
        ("Ciencia de Datos", "Análisis, Python y Machine Learning"),
        ("Desarrollo Web", "Frontend, Backend y Bases de Datos"),
        ("Productividad Digital", "Herramientas en la nube y automatización"),
    ]
    cur.executemany("INSERT INTO categorias_curso (nombre, descripcion) VALUES (?, ?)", categorias)

    # 3. Cursos
    cursos = [
        ("Python y SQLite para Análisis de Datos", "Domina consultas y modelos.", 1, 1, "intermedio", 499.0, 18.0, "publicado"),
        ("Introducción a Machine Learning", "Algoritmos supervisados desde cero.", 1, 1, "avanzado", 799.0, 28.0, "publicado"),
        ("Desarrollo Web con Streamlit", "Crea dashboards interactivos.", 2, 2, "basico", 0.0, 10.0, "publicado"),
        ("Herramientas Colaborativas en la Nube", "Flujos de trabajo eficientes.", 3, 2, "basico", 299.0, 8.0, "publicado"),
        ("Redes IPv6 y Enrutamiento OSPF", "Configuración práctica de redes.", 3, 3, "avanzado", 650.0, 24.0, "publicado"),
    ]
    cur.executemany(
        """INSERT INTO cursos 
           (titulo, descripcion, id_categoria, id_instructor, nivel, precio, duracion_horas, estatus) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        cursos,
    )

    # 4. Inscripciones históricas (patrón: bajo progreso + cursos largos/avanzados = mayor deserción)
    inscripciones = [
        (4, 1, 95.0, "completada"),
        (5, 1, 15.0, "abandonada"),
        (6, 1, 82.0, "activa"),
        (7, 2, 10.0, "abandonada"),
        (8, 2, 20.0, "abandonada"),
        (9, 2, 92.0, "completada"),
        (4, 3, 100.0, "completada"),
        (5, 3, 85.0, "activa"),
        (6, 3, 12.0, "abandonada"),
        (7, 4, 100.0, "completada"),
        (8, 4, 78.0, "activa"),
        (9, 4, 18.0, "abandonada"),
        (4, 5, 14.0, "abandonada"),
        (8, 5, 88.0, "completada"),
    ]
    cur.executemany(
        "INSERT INTO inscripciones (id_usuario, id_curso, progreso, estatus) VALUES (?, ?, ?, ?)",
        inscripciones,
    )

    con.commit()
    con.close()


inicializar_datos_demo()

st.title("🎓 Plataforma E-Learning: Gestión Integral y Analítica Predictiva")

tab_cursos, tab_usuarios, tab_pred = st.tabs(
    ["📋 CRUD de Cursos", "👥 CRUD de Usuarios (Instructores/Alumnos)", "🤖 Predicción de Deserción (ML)"]
)

# =====================================================================
# PESTAÑA 1: CRUD DE CURSOS + KPIs + GRÁFICAS + INSCRIPCIÓN RÁPIDA
# =====================================================================
with tab_cursos:
    con = get_connection("elearning_cursos")

    df_categorias = pd.read_sql("SELECT id_categoria, nombre FROM categorias_curso", con)
    df_instructores = pd.read_sql(
        "SELECT id_usuario, nombre || ' ' || apellidos AS instructor FROM usuarios WHERE rol = 'instructor' AND activo = 1",
        con,
    )
    df_estudiantes = pd.read_sql(
        "SELECT id_usuario, nombre || ' ' || apellidos AS estudiante FROM usuarios WHERE rol = 'estudiante' AND activo = 1",
        con,
    )

    df_cursos = pd.read_sql(
        """
        SELECT c.id_curso AS ID,
               c.titulo AS Título,
               cat.nombre AS Categoría,
               u.nombre || ' ' || u.apellidos AS Instructor,
               c.nivel AS Nivel,
               c.precio AS Precio,
               c.duracion_horas AS Horas,
               c.estatus AS Estatus,
               COUNT(i.id_inscripcion) AS Inscritos,
               ROUND(COALESCE(AVG(i.progreso), 0), 1) AS Progreso_Prom
        FROM cursos c
        JOIN categorias_curso cat ON c.id_categoria = cat.id_categoria
        JOIN usuarios u ON c.id_instructor = u.id_usuario
        LEFT JOIN inscripciones i ON c.id_curso = i.id_curso
        GROUP BY c.id_curso
        ORDER BY c.id_curso DESC
        """,
        con,
    )

    df_insc_stats = pd.read_sql("SELECT progreso, estatus FROM inscripciones", con)

    # --- KPIs Ejecutivos ---
    cursos_pub = int((df_cursos["Estatus"] == "publicado").sum()) if not df_cursos.empty else 0
    total_insc = len(df_insc_stats)
    tasa_abandono = (
        float((df_insc_stats["estatus"] == "abandonada").mean() * 100) if total_insc > 0 else 0.0
    )
    prog_global = float(df_insc_stats["progreso"].mean()) if total_insc > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cursos Publicados", cursos_pub)
    k2.metric("Inscripciones Totales", total_insc)
    k3.metric("Tasa de Deserción", f"{tasa_abandono:.1f}%")
    k4.metric("Progreso Promedio", f"{prog_global:.1f}%")

    # --- Gráficas de Distribución ---
    if not df_cursos.empty and not df_insc_stats.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Cursos por Categoría")
            st.bar_chart(df_cursos["Categoría"].value_counts(), height=220)
        with g2:
            st.caption("Estatus de Inscripciones Estudiantiles")
            st.bar_chart(df_insc_stats["estatus"].value_counts(), height=220)

    # --- Tabla Principal (READ) + Descarga CSV ---
    st.subheader("Catálogo Actual de Cursos")
    st.dataframe(df_cursos, use_container_width=True, hide_index=True)

    csv_cursos = df_cursos.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Exportar Catálogo de Cursos a CSV",
        data=csv_cursos,
        file_name="reporte_cursos_elearning.csv",
        mime="text/csv",
    )

    # --- Registro Rápido de Inscripción / Progreso (para alimentar ML) ---
    with st.expander("📝 Registrar o Actualizar Inscripción de Alumno (Alimenta el modelo ML)"):
        if not df_cursos.empty and not df_estudiantes.empty:
            with st.form("form_inscripcion_rapida", clear_on_submit=True):
                ci1, ci2, ci3, ci4, ci5 = st.columns([2, 2, 1, 1, 1])
                est_sel = ci1.selectbox("Estudiante", df_estudiantes["estudiante"])
                cur_opc = {f"{r['ID']} - {r['Título']}": r["ID"] for _, r in df_cursos.iterrows()}
                cur_sel = ci2.selectbox("Curso", list(cur_opc.keys()))
                prog_val = ci3.number_input("Progreso (%)", min_value=0.0, max_value=100.0, value=30.0, step=5.0)
                est_insc = ci4.selectbox("Estatus", ["activa", "completada", "abandonada"])
                btn_insc = ci5.form_submit_button("Guardar", use_container_width=True)

                if btn_insc:
                    id_est = int(df_estudiantes.loc[df_estudiantes["estudiante"] == est_sel, "id_usuario"].values[0])
                    id_cur = cur_opc[cur_sel]
                    cur = con.cursor()
                    cur.execute(
                        """INSERT INTO inscripciones (id_usuario, id_curso, progreso, estatus)
                           VALUES (?, ?, ?, ?)
                           ON CONFLICT(id_usuario, id_curso) 
                           DO UPDATE SET progreso = excluded.progreso, estatus = excluded.estatus""",
                        (id_est, id_cur, prog_val, est_insc),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Inscripción guardada/actualizada. Dataset ML sincronizado.")
                    st.rerun()

    st.divider()
    col_create, col_update, col_delete = st.columns(3)

    # --- CREATE CURSO ---
    with col_create:
        st.subheader("➕ Nuevo Curso")
        with st.form("form_crear_curso", clear_on_submit=True):
            titulo = st.text_input("Título del curso*")
            descripcion = st.text_area("Descripción", height=68)
            cat_nombre = st.selectbox("Categoría", df_categorias["nombre"])
            inst_nombre = st.selectbox("Instructor", df_instructores["instructor"])
            nivel = st.selectbox("Nivel", ["basico", "intermedio", "avanzado"])
            precio = st.number_input("Precio ($ MXN)", min_value=0.0, step=50.0)
            horas = st.number_input("Duración (horas)", min_value=1.0, value=10.0, step=1.0)
            estatus = st.selectbox("Estatus", ["borrador", "publicado", "archivado"])

            if st.form_submit_button("Guardar Curso", use_container_width=True):
                if not titulo.strip():
                    st.error("El título es obligatorio.")
                elif df_instructores.empty:
                    st.error("No hay instructores activos registrados.")
                else:
                    id_cat = int(df_categorias.loc[df_categorias["nombre"] == cat_nombre, "id_categoria"].values[0])
                    id_inst = int(df_instructores.loc[df_instructores["instructor"] == inst_nombre, "id_usuario"].values[0])
                    cur = con.cursor()
                    cur.execute(
                        """INSERT INTO cursos 
                           (titulo, descripcion, id_categoria, id_instructor, nivel, precio, duracion_horas, estatus)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (titulo.strip(), descripcion.strip(), id_cat, id_inst, nivel, precio, horas, estatus),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Curso creado correctamente.")
                    st.rerun()

    # --- UPDATE CURSO ---
    with col_update:
        st.subheader("✏️ Editar Curso")
        if not df_cursos.empty:
            opciones_edit = {f"{r['ID']} - {r['Título']}": r["ID"] for _, r in df_cursos.iterrows()}
            seleccion_edit = st.selectbox("Selecciona curso a editar", list(opciones_edit.keys()))
            id_edit = opciones_edit[seleccion_edit]
            curso_actual = df_cursos[df_cursos["ID"] == id_edit].iloc[0]

            with st.form("form_editar_curso"):
                nuevo_titulo = st.text_input("Título", value=curso_actual["Título"])
                niveles = ["basico", "intermedio", "avanzado"]
                nuevo_nivel = st.selectbox("Nivel", niveles, index=niveles.index(curso_actual["Nivel"]))
                nuevo_precio = st.number_input("Precio ($)", min_value=0.0, value=float(curso_actual["Precio"]), step=50.0)
                nueva_duracion = st.number_input("Horas", min_value=1.0, value=float(curso_actual["Horas"] or 1.0), step=1.0)
                estatus_list = ["borrador", "publicado", "archivado"]
                nuevo_estatus = st.selectbox("Estatus", estatus_list, index=estatus_list.index(curso_actual["Estatus"]))

                if st.form_submit_button("Actualizar Curso", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        """UPDATE cursos 
                           SET titulo = ?, nivel = ?, precio = ?, duracion_horas = ?, estatus = ?
                           WHERE id_curso = ?""",
                        (nuevo_titulo.strip(), nuevo_nivel, nuevo_precio, nueva_duracion, nuevo_estatus, id_edit),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Curso actualizado.")
                    st.rerun()

    # --- DELETE CURSO ---
    with col_delete:
        st.subheader("🗑️ Eliminar Curso")
        if not df_cursos.empty:
            opciones_del = {f"{r['ID']} - {r['Título']}": r["ID"] for _, r in df_cursos.iterrows()}
            seleccion_del = st.selectbox("Selecciona curso a eliminar", list(opciones_del.keys()))
            id_del = opciones_del[seleccion_del]

            st.caption("Nota: SQLite bloqueará el borrado si el curso ya tiene alumnos inscritos.")
            if st.button("Eliminar Definitivamente", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM cursos WHERE id_curso = ?", (id_del,))
                    con.commit()
                    st.cache_data.clear()
                    st.success("Curso eliminado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: existen inscripciones vinculadas a este curso.")

    con.close()


# =====================================================================
# PESTAÑA 2: CRUD DE USUARIOS (INSTRUCTORES Y ESTUDIANTES)
# =====================================================================
with tab_usuarios:
    con = get_connection("elearning_cursos")

    st.subheader("Directorio de Usuarios de la Plataforma")
    df_users = pd.read_sql(
        """
        SELECT u.id_usuario AS ID,
               u.nombre AS Nombre,
               u.apellidos AS Apellidos,
               u.correo AS Correo,
               u.rol AS Rol,
               COALESCE(u.biografia, '') AS Biografía,
               CASE WHEN u.activo = 1 THEN 'Activo' ELSE 'Inactivo' END AS Estado,
               COUNT(DISTINCT c.id_curso) AS Cursos_Impartidos,
               COUNT(DISTINCT i.id_inscripcion) AS Cursos_Inscritos
        FROM usuarios u
        LEFT JOIN cursos c ON u.id_usuario = c.id_instructor
        LEFT JOIN inscripciones i ON u.id_usuario = i.id_usuario
        GROUP BY u.id_usuario
        ORDER BY u.rol DESC, u.id_usuario ASC
        """,
        con,
    )
    st.dataframe(df_users, use_container_width=True, hide_index=True)

    st.divider()
    col_uc, col_uu, col_ud = st.columns(3)

    # --- CREATE USUARIO ---
    with col_uc:
        st.subheader("➕ Nuevo Usuario")
        with st.form("form_crear_usuario", clear_on_submit=True):
            u_nom = st.text_input("Nombre*")
            u_ape = st.text_input("Apellidos*")
            u_correo = st.text_input("Correo electrónico*")
            u_rol = st.selectbox("Rol en plataforma", ["estudiante", "instructor", "administrador"])
            u_bio = st.text_area("Biografía (opcional)", height=68)
            u_act = st.checkbox("Usuario activo", value=True)

            if st.form_submit_button("Registrar Usuario", use_container_width=True):
                if not u_nom.strip() or not u_ape.strip() or not u_correo.strip():
                    st.error("Nombre, apellidos y correo son obligatorios.")
                else:
                    try:
                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO usuarios (nombre, apellidos, correo, contrasena_hash, rol, biografia, activo)
                               VALUES (?, ?, ?, 'hash_demo', ?, ?, ?)""",
                            (u_nom.strip(), u_ape.strip(), u_correo.strip(), u_rol, u_bio.strip() or None, int(u_act)),
                        )
                        con.commit()
                        st.success("Usuario registrado correctamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ese correo electrónico ya está registrado.")

    # --- UPDATE USUARIO ---
    with col_uu:
        st.subheader("✏️ Editar Usuario")
        if not df_users.empty:
            opc_u = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']} ({r['Rol']})": r["ID"] for _, r in df_users.iterrows()}
            sel_u = st.selectbox("Selecciona usuario", list(opc_u.keys()))
            id_u_edit = opc_u[sel_u]
            user_act = df_users[df_users["ID"] == id_u_edit].iloc[0]

            with st.form("form_editar_usuario"):
                roles_u = ["estudiante", "instructor", "administrador"]
                edit_u_rol = st.selectbox("Rol", roles_u, index=roles_u.index(user_act["Rol"]))
                edit_u_bio = st.text_area("Biografía", value=user_act["Biografía"], height=68)
                edit_u_act = st.checkbox("Usuario activo", value=(user_act["Estado"] == "Activo"))

                if st.form_submit_button("Guardar Cambios", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        "UPDATE usuarios SET rol = ?, biografia = ?, activo = ? WHERE id_usuario = ?",
                        (edit_u_rol, edit_u_bio.strip() or None, int(edit_u_act), id_u_edit),
                    )
                    con.commit()
                    st.success("Usuario actualizado.")
                    st.rerun()

    # --- DELETE USUARIO ---
    with col_ud:
        st.subheader("🗑️ Eliminar Usuario")
        if not df_users.empty:
            opc_udel = {f"{r['ID']} - {r['Nombre']} {r['Apellidos']}": r["ID"] for _, r in df_users.iterrows()}
            sel_udel = st.selectbox("Usuario a eliminar", list(opc_udel.keys()))
            id_u_del = opc_udel[sel_udel]

            st.caption("Nota: SQLite bloqueará el borrado si el usuario imparte cursos o tiene inscripciones.")
            if st.button("Eliminar Usuario", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM usuarios WHERE id_usuario = ?", (id_u_del,))
                    con.commit()
                    st.cache_data.clear()
                    st.success("Usuario eliminado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: el usuario tiene cursos o inscripciones vinculadas.")

    con.close()


# =====================================================================
# PESTAÑA 3: MODELO PREDICTIVO CON EXPLICABILIDAD
# =====================================================================
with tab_pred:
    st.subheader("Simulador de Riesgo de Abandono de Curso")
    st.write(
        "Entrena un clasificador **Random Forest** usando el historial de `inscripciones` y `cursos` "
        "para estimar si un alumno abandonará un curso."
    )

    @st.cache_data
    def obtener_dataset_ml():
        con = get_connection("elearning_cursos")
        query = """
            SELECT i.progreso,
                   i.estatus,
                   c.precio,
                   COALESCE(c.duracion_horas, 10) AS duracion_horas,
                   c.nivel
            FROM inscripciones i
            JOIN cursos c ON i.id_curso = c.id_curso
        """
        df = pd.read_sql(query, con)
        con.close()
        return df

    df_ml = obtener_dataset_ml()

    if len(df_ml) < 5 or df_ml["estatus"].eq("abandonada").nunique() < 2:
        st.warning("Se requieren al menos 5 inscripciones con estatus variados (abandonadas y activas/completadas) para entrenar.")
    else:
        le_nivel = LabelEncoder()
        df_ml["nivel_cod"] = le_nivel.fit_transform(df_ml["nivel"])
        df_ml["target_abandono"] = (df_ml["estatus"] == "abandonada").astype(int)

        features = ["progreso", "precio", "duracion_horas", "nivel_cod"]
        X = df_ml[features]
        y = df_ml["target_abandono"]

        modelo = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        modelo.fit(X, y)

        col_sim, col_res = st.columns(2)

        with col_sim:
            st.markdown("#### Parámetros del Estudiante y Curso")
            in_progreso = st.slider("Progreso actual del alumno (%)", 0, 100, 25)
            in_precio = st.number_input("Precio del curso ($ MXN)", min_value=0.0, value=499.0, step=50.0)
            in_horas = st.slider("Duración total del curso (horas)", 1, 60, 18)
            in_nivel = st.selectbox("Nivel de dificultad", le_nivel.classes_)

            predecir = st.button("Calcular Riesgo de Deserción", type="primary", use_container_width=True)

        with col_res:
            st.markdown("#### Resultado de la Predicción")
            if predecir:
                nivel_num = le_nivel.transform([in_nivel])[0]
                entrada = pd.DataFrame(
                    [[in_progreso, in_precio, in_horas, nivel_num]],
                    columns=features,
                )
                idx_clase_1 = list(modelo.classes_).index(1)
                prob_abandono = modelo.predict_proba(entrada)[0][idx_clase_1]

                st.metric("Probabilidad de Abandono", f"{prob_abandono * 100:.1f}%")

                if prob_abandono >= 0.5:
                    st.error("⚠️ **Alto riesgo de deserción.** Se sugiere enviar recordatorio o tutoría personalizada.")
                else:
                    st.success("✅ **Baja probabilidad de abandono.** El estudiante muestra buen ritmo de avance.")

        st.divider()
        exp1, exp2 = st.columns(2)

        with exp1:
            st.markdown("#### Importancia de Variables en el Modelo")
            df_imp = pd.DataFrame(
                {
                    "Variable": ["Progreso (%)", "Precio del Curso", "Duración (Horas)", "Nivel Dificultad"],
                    "Importancia": modelo.feature_importances_,
                }
            ).set_index("Variable")
            st.bar_chart(df_imp, height=230)

        with exp2:
            st.markdown("#### Tasa Histórica de Abandono por Nivel")
            resumen_nivel = (
                df_ml.groupby("nivel")["target_abandono"]
                .agg(Inscripciones="count", Abandonos="sum")
                .reset_index()
            )
            resumen_nivel["Deserción (%)"] = (resumen_nivel["Abandonos"] / resumen_nivel["Inscripciones"] * 100).round(1)
            st.dataframe(resumen_nivel, use_container_width=True, hide_index=True)

