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

    # Verificar si ya existen usuarios
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] > 0:
        con.close()
        return

    # 1. Usuarios (2 instructores, 6 estudiantes)
    usuarios = [
        ("Carlos", "Mendoza", "carlos.inst@edu.mx", "hash123", "instructor"),
        ("Laura", "Gómez", "laura.inst@edu.mx", "hash123", "instructor"),
        ("Ana", "Torres", "ana@alumno.mx", "hash123", "estudiante"),
        ("Luis", "Ramírez", "luis@alumno.mx", "hash123", "estudiante"),
        ("Sofía", "Hernández", "sofia@alumno.mx", "hash123", "estudiante"),
        ("Diego", "Vargas", "diego@alumno.mx", "hash123", "estudiante"),
        ("Valeria", "Cruz", "valeria@alumno.mx", "hash123", "estudiante"),
        ("Jorge", "Silva", "jorge@alumno.mx", "hash123", "estudiante"),
    ]
    cur.executemany(
        "INSERT INTO usuarios (nombre, apellidos, correo, contrasena_hash, rol) VALUES (?, ?, ?, ?, ?)",
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
        ("Introducción a Machine Learning", "Algoritmos supervisados desde cero.", 1, 1, "avanzado", 799.0, 25.0, "publicado"),
        ("Desarrollo Web con Streamlit", "Crea dashboards interactivos.", 2, 2, "basico", 0.0, 10.0, "publicado"),
        ("Herramientas Colaborativas en la Nube", "Flujos de trabajo eficientes.", 3, 2, "basico", 299.0, 8.0, "publicado"),
    ]
    cur.executemany(
        """INSERT INTO cursos 
           (titulo, descripcion, id_categoria, id_instructor, nivel, precio, duracion_horas, estatus) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        cursos,
    )

    # 4. Inscripciones históricas (patrón: bajo progreso + cursos largos/caros = mayor abandono)
    inscripciones = [
        (3, 1, 95.0, "completada"),
        (4, 1, 15.0, "abandonada"),
        (5, 1, 80.0, "activa"),
        (6, 2, 10.0, "abandonada"),
        (7, 2, 20.0, "abandonada"),
        (8, 2, 90.0, "completada"),
        (3, 3, 100.0, "completada"),
        (4, 3, 85.0, "activa"),
        (5, 3, 12.0, "abandonada"),
        (6, 4, 100.0, "completada"),
        (7, 4, 75.0, "activa"),
        (8, 4, 18.0, "abandonada"),
    ]
    cur.executemany(
        "INSERT INTO inscripciones (id_usuario, id_curso, progreso, estatus) VALUES (?, ?, ?, ?)",
        inscripciones,
    )

    con.commit()
    con.close()


inicializar_datos_demo()

# =====================================================================
# 2. INTERFAZ PRINCIPAL CON PESTAÑAS (CRUD + PREDICCIONES)
# =====================================================================
st.title("🎓 Plataforma E-Learning: Gestión y Analítica Predictiva")

tab_crud, tab_pred = st.tabs(["📋 CRUD de Cursos", "🤖 Predicción de Deserción (ML)"])

# ---------------------------------------------------------------------
# PESTAÑA 1: CRUD COMPLETO SOBRE LA TABLA `cursos`
# ---------------------------------------------------------------------
with tab_crud:
    con = get_connection("elearning_cursos")

    # Cargar catálogos para llaves foráneas
    df_categorias = pd.read_sql("SELECT id_categoria, nombre FROM categorias_curso", con)
    df_instructores = pd.read_sql(
        "SELECT id_usuario, nombre || ' ' || apellidos AS instructor FROM usuarios WHERE rol = 'instructor'",
        con,
    )

    # --- READ (Lectura con JOIN) ---
    st.subheader("Catálogo Actual de Cursos")
    query_cursos = """
        SELECT c.id_curso AS ID,
               c.titulo AS Título,
               cat.nombre AS Categoría,
               u.nombre || ' ' || u.apellidos AS Instructor,
               c.nivel AS Nivel,
               c.precio AS Precio,
               c.duracion_horas AS Horas,
               c.estatus AS Estatus
        FROM cursos c
        JOIN categorias_curso cat ON c.id_categoria = cat.id_categoria
        JOIN usuarios u ON c.id_instructor = u.id_usuario
        ORDER BY c.id_curso DESC
    """
    df_cursos = pd.read_sql(query_cursos, con)
    st.dataframe(df_cursos, use_container_width=True, hide_index=True)

    st.divider()
    col_create, col_update, col_delete = st.columns(3)

    # --- CREATE (Crear nuevo curso) ---
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
                    st.success("Curso creado correctamente.")
                    st.rerun()

    # --- UPDATE (Actualizar curso existente) ---
    with col_update:
        st.subheader("✏️ Editar Curso")
        if not df_cursos.empty:
            opciones_edit = {f"{row['ID']} - {row['Título']}": row["ID"] for _, row in df_cursos.iterrows()}
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
                    st.success("Curso actualizado.")
                    st.rerun()

    # --- DELETE (Eliminar curso) ---
    with col_delete:
        st.subheader("🗑️ Eliminar Curso")
        if not df_cursos.empty:
            opciones_del = {f"{row['ID']} - {row['Título']}": row["ID"] for _, row in df_cursos.iterrows()}
            seleccion_del = st.selectbox("Selecciona curso a eliminar", list(opciones_del.keys()))
            id_del = opciones_del[seleccion_del]

            st.caption("Nota: Si el curso ya tiene alumnos inscritos, SQLite bloqueará el borrado por integridad referencial.")
            if st.button("Eliminar Definitivamente", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM cursos WHERE id_curso = ?", (id_del,))
                    con.commit()
                    st.success("Curso eliminado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: existen inscripciones vinculadas a este curso.")

    con.close()


# ---------------------------------------------------------------------
# PESTAÑA 2: MODELO PREDICTIVO (RIESGO DE DESERCIÓN ESTUDIANTIL)
# ---------------------------------------------------------------------
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

    if len(df_ml) < 5 or df_ml["estatus"].nunique() < 2:
        st.warning("Se necesitan más registros variados en `inscripciones` para entrenar el modelo.")
    else:
        # Preprocesamiento
        le_nivel = LabelEncoder()
        df_ml["nivel_cod"] = le_nivel.fit_transform(df_ml["nivel"])
        df_ml["target_abandono"] = (df_ml["estatus"] == "abandonada").astype(int)

        X = df_ml[["progreso", "precio", "duracion_horas", "nivel_cod"]]
        y = df_ml["target_abandono"]

        modelo = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        modelo.fit(X, y)

        col_sim, col_res = st.columns([1, 1])

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
                    columns=["progreso", "precio", "duracion_horas", "nivel_cod"],
                )
                prob_abandono = modelo.predict_proba(entrada)[0][1]

                st.metric("Probabilidad de Abandono", f"{prob_abandono * 100:.1f}%")

                if prob_abandono >= 0.5:
                    st.error("⚠️ **Alto riesgo de deserción.** Se sugiere enviar recordatorio o tutoría.")
                else:
                    st.success("✅ **Baja probabilidad de abandono.** El estudiante muestra buen ritmo.")

                with st.expander("Ver datos históricos usados para entrenar"):
                    st.dataframe(df_ml[["progreso", "precio", "duracion_horas", "nivel", "estatus"]], use_container_width=True)

