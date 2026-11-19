import sqlite3
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection
from datos_demo import agregar_registros_demo
from interfaz import render_kpi_cards, render_page_header, render_sidebar

st.set_page_config(page_title="Mercado Libre | Predicciones", page_icon="🛒", layout="wide")
render_sidebar("Mercado Libre", "Administra publicaciones y vendedores, y consulta la predicción de demanda.")


# =====================================================================
# 1. POBLADO INICIAL DE DATOS (Solo si la BD está vacía)
# =====================================================================
def inicializar_datos_demo():
    con = get_connection("mercado_libre")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] > 0:
        con.close()
        return

    # 1. Usuarios (vendedores con distinta reputación y compradores)
    usuarios = [
        ("TECH_STORE_MX", "Ricardo", "Salinas", "ventas@techstore.mx", "5510001001", "hash1", "vendedor", 4.9, 1),
        ("GADGETS_EXPRESS", "Mónica", "Núñez", "monica@gadgets.mx", "5510001002", "hash2", "vendedor", 4.2, 1),
        ("BAZAR_USADOS", "Tomás", "Aguilar", "tomas@bazar.mx", "5510001003", "hash3", "vendedor", 3.1, 1),
        ("COMPRADOR_01", "Paola", "Ríos", "paola@mail.com", "5510001004", "hash4", "comprador", 5.0, 1),
        ("COMPRADOR_02", "Fernando", "Lara", "fer@mail.com", "5510001005", "hash5", "comprador", 4.8, 1),
    ]
    cur.executemany(
        """INSERT INTO usuarios 
           (nickname, nombre, apellidos, correo, telefono, contrasena_hash, tipo_usuario, reputacion, activo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        usuarios,
    )

    # 2. Dirección de envío para pedidos
    cur.execute(
        """INSERT INTO direcciones (id_usuario, calle, num_exterior, colonia, ciudad, estado, codigo_postal, es_principal)
           VALUES (4, 'Av. Universidad', '120', 'Centro', 'Cuautitlán Izcalli', 'Estado de México', '54700', 1)"""
    )

    # 3. Categorías
    categorias = [("Electrónica",), ("Cómputo y Accesorios",), ("Hogar y Oficina",)]
    cur.executemany("INSERT INTO categorias (nombre) VALUES (?)", categorias)

    # 4. Publicaciones
    publicaciones = [
        (1, 2, "Teclado Mecánico RGB Switch Red", "Teclado gamer compacto", 899.0, 25, "nuevo", "premium", 1, "activa"),
        (1, 2, "Mouse Inalámbrico Ergonómico", "Sensor óptico 16000 DPI", 549.0, 40, "nuevo", "premium", 1, "activa"),
        (1, 1, "Audífonos Bluetooth Cancelación Ruido", "Batería 30 horas", 1299.0, 15, "nuevo", "clasica", 1, "activa"),
        (2, 2, "Hub USB-C 7 en 1 HDMI 4K", "Adaptador aluminio", 420.0, 30, "nuevo", "clasica", 0, "activa"),
        (2, 3, "Lámpara LED Escritorio Flexible", "3 tonos de luz", 280.0, 18, "nuevo", "gratuita", 0, "activa"),
        (3, 1, "Monitor 24 Pulgadas IPS 75Hz", "Detalle estético leve", 1650.0, 5, "usado", "clasica", 0, "activa"),
        (3, 2, "Tarjeta Gráfica RX 580 8GB", "Mantenimiento recién hecho", 2100.0, 3, "reacondicionado", "premium", 1, "activa"),
        (3, 3, "Silla de Oficina Básica", "Poco uso", 950.0, 4, "usado", "gratuita", 0, "activa"),
    ]
    cur.executemany(
        """INSERT INTO publicaciones 
           (id_vendedor, id_categoria, titulo, descripcion, precio, stock, condicion, tipo_publicacion, envio_gratis, estatus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        publicaciones,
    )

    # 5. Pedidos y Detalle de Pedidos
    pedidos = [
        (4, 1, "entregado", 16182.0),
        (5, 1, "entregado", 13176.0),
        (4, 1, "pagado", 15588.0),
        (5, 1, "entregado", 3780.0),
        (4, 1, "entregado", 1400.0),
        (5, 1, "entregado", 4950.0),
        (4, 1, "pagado", 14700.0),
        (5, 1, "entregado", 1900.0),
    ]
    cur.executemany(
        "INSERT INTO pedidos (id_comprador, id_direccion_envio, estatus, total) VALUES (?, ?, ?, ?)",
        pedidos,
    )

    detalles = [
        (1, 1, 18, 899.0),
        (2, 2, 24, 549.0),
        (3, 3, 12, 1299.0),
        (4, 4, 9, 420.0),
        (5, 5, 5, 280.0),
        (6, 6, 3, 1650.0),
        (7, 7, 7, 2100.0),
        (8, 8, 2, 950.0),
    ]
    cur.executemany(
        "INSERT INTO detalle_pedido (id_pedido, id_publicacion, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
        detalles,
    )

    con.commit()
    con.close()


inicializar_datos_demo()
if agregar_registros_demo("mercado_libre"):
    st.cache_data.clear()

render_page_header(
    "🛒 Mercado Libre",
    "Administra publicaciones y vendedores; explora indicadores y demanda estimada.",
)

tab_pub, tab_vend, tab_pred = st.tabs(
    ["📋 Publicaciones", "🏪 Vendedores", "🤖 Predicción de Demanda"]
)

# =====================================================================
# PESTAÑA 1: CRUD DE PUBLICACIONES + KPIs + GRÁFICAS + EXPORTACIÓN CSV
# =====================================================================
with tab_pub:
    con = get_connection("mercado_libre")

    df_vendedores = pd.read_sql(
        """SELECT id_usuario, nickname || ' (Rep: ' || reputacion || ')' AS vendedor 
           FROM usuarios WHERE tipo_usuario IN ('vendedor','ambos') AND activo = 1""",
        con,
    )
    df_categorias = pd.read_sql("SELECT id_categoria, nombre FROM categorias", con)

    df_pub = pd.read_sql(
        """
        SELECT p.id_publicacion AS ID,
               p.titulo AS Título,
               u.nickname AS Vendedor,
               u.reputacion AS Reputación,
               c.nombre AS Categoría,
               p.precio AS Precio,
               p.stock AS Stock,
               p.condicion AS Condición,
               p.tipo_publicacion AS Tipo,
               p.envio_gratis AS Envío_Gratis,
               p.estatus AS Estatus,
               COALESCE(SUM(dp.cantidad), 0) AS Unidades_Vendidas
        FROM publicaciones p
        JOIN usuarios u ON p.id_vendedor = u.id_usuario
        JOIN categorias c ON p.id_categoria = c.id_categoria
        LEFT JOIN detalle_pedido dp ON p.id_publicacion = dp.id_publicacion
        GROUP BY p.id_publicacion
        ORDER BY p.id_publicacion DESC
        """,
        con,
    )

    # --- KPIs Ejecutivos ---
    pub_activas = int((df_pub["Estatus"] == "activa").sum()) if not df_pub.empty else 0
    stock_total = int(df_pub["Stock"].sum()) if not df_pub.empty else 0
    unidades_totales = int(df_pub["Unidades_Vendidas"].sum()) if not df_pub.empty else 0
    ingresos_totales = float((df_pub["Precio"] * df_pub["Unidades_Vendidas"]).sum()) if not df_pub.empty else 0.0

    render_kpi_cards(
        [
            ("Publicaciones activas", pub_activas),
            ("Stock disponible", f"{stock_total} u."),
            ("Unidades vendidas", f"{unidades_totales} u."),
            ("Ingresos históricos", f"${ingresos_totales:,.2f}"),
        ]
    )

    # --- Gráficas de Distribución ---
    if not df_pub.empty:
        g1, g2 = st.columns(2)
        with g1:
            with st.container(border=True):
                st.markdown("#### Publicaciones por categoría")
                st.bar_chart(df_pub["Categoría"].value_counts(), height=220)
        with g2:
            with st.container(border=True):
                st.markdown("#### Nivel de exposición")
                st.bar_chart(df_pub["Tipo"].value_counts(), height=220)

    # --- Tabla Principal (READ) + Descarga CSV ---
    st.subheader("Catálogo General de Publicaciones")
    st.dataframe(df_pub, use_container_width=True, hide_index=True)

    csv_pub = df_pub.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Exportar Catálogo a CSV",
        data=csv_pub,
        file_name="reporte_publicaciones_ml.csv",
        mime="text/csv",
    )

    # --- Registro Rápido de Venta (para alimentar `detalle_pedido` en vivo) ---
    with st.expander("💸 Registrar Venta de una Publicación (Alimenta el historial ML)"):
        if not df_pub.empty:
            with st.form("form_venta_rapida", clear_on_submit=True):
                col_v1, col_v2, col_v3 = st.columns([2, 1, 1])
                opciones_v = {f"{r['ID']} - {r['Título']} (${r['Precio']})": r["ID"] for _, r in df_pub.iterrows()}
                pub_v_sel = col_v1.selectbox("Publicación vendida", list(opciones_v.keys()))
                cant_v = col_v2.number_input("Cantidad vendida", min_value=1, value=5, step=1)
                btn_v = col_v3.form_submit_button("Registrar Pedido", use_container_width=True)

                if btn_v:
                    id_pub_v = opciones_v[pub_v_sel]
                    precio_v = float(df_pub.loc[df_pub["ID"] == id_pub_v, "Precio"].values[0])
                    total_v = precio_v * cant_v
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO pedidos (id_comprador, id_direccion_envio, estatus, total) VALUES (4, 1, 'entregado', ?)",
                        (total_v,),
                    )
                    id_ped = cur.lastrowid
                    cur.execute(
                        "INSERT INTO detalle_pedido (id_pedido, id_publicacion, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                        (id_ped, id_pub_v, cant_v, precio_v),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success(f"Venta registrada (+{cant_v} unidades). Modelo predictivo actualizado.")
                    st.rerun()

    st.divider()
    col_c, col_u, col_d = st.columns(3)

    # --- CREATE PUBLICACIÓN ---
    with col_c:
        st.subheader("➕ Nueva Publicación")
        with st.form("form_crear_pub", clear_on_submit=True):
            titulo = st.text_input("Título del producto*")
            vend_sel = st.selectbox("Vendedor", df_vendedores["vendedor"])
            cat_sel = st.selectbox("Categoría", df_categorias["nombre"])
            precio = st.number_input("Precio ($ MXN)", min_value=1.0, value=500.0, step=50.0)
            stock = st.number_input("Stock disponible", min_value=0, value=10, step=1)
            condicion = st.selectbox("Condición", ["nuevo", "usado", "reacondicionado"])
            tipo_pub = st.selectbox("Tipo de publicación", ["gratuita", "clasica", "premium"])
            envio_gratis = st.checkbox("Ofrecer envío gratis", value=True)

            if st.form_submit_button("Publicar Artículo", use_container_width=True):
                if not titulo.strip():
                    st.error("El título es obligatorio.")
                elif df_vendedores.empty:
                    st.error("No hay vendedores activos disponibles.")
                else:
                    id_vend = int(df_vendedores.loc[df_vendedores["vendedor"] == vend_sel, "id_usuario"].values[0])
                    id_cat = int(df_categorias.loc[df_categorias["nombre"] == cat_sel, "id_categoria"].values[0])
                    cur = con.cursor()
                    cur.execute(
                        """INSERT INTO publicaciones 
                           (id_vendedor, id_categoria, titulo, precio, stock, condicion, tipo_publicacion, envio_gratis)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (id_vend, id_cat, titulo.strip(), precio, stock, condicion, tipo_pub, int(envio_gratis)),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Publicación creada.")
                    st.rerun()

    # --- UPDATE PUBLICACIÓN ---
    with col_u:
        st.subheader("✏️ Editar Publicación")
        if not df_pub.empty:
            opciones_u = {f"{r['ID']} - {r['Título']}": r["ID"] for _, r in df_pub.iterrows()}
            sel_u = st.selectbox("Selecciona publicación", list(opciones_u.keys()))
            id_u = opciones_u[sel_u]
            actual = df_pub[df_pub["ID"] == id_u].iloc[0]

            with st.form("form_edit_pub"):
                nuevo_precio = st.number_input("Precio ($)", min_value=1.0, value=float(actual["Precio"]), step=50.0)
                nuevo_stock = st.number_input("Stock", min_value=0, value=int(actual["Stock"]), step=1)
                tipos = ["gratuita", "clasica", "premium"]
                nuevo_tipo = st.selectbox("Tipo", tipos, index=tipos.index(actual["Tipo"]))
                nuevo_envio = st.checkbox("Envío gratis", value=bool(actual["Envío_Gratis"]))
                estados = ["activa", "pausada", "finalizada"]
                nuevo_est = st.selectbox("Estatus", estados, index=estados.index(actual["Estatus"]))

                if st.form_submit_button("Guardar Cambios", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        """UPDATE publicaciones 
                           SET precio = ?, stock = ?, tipo_publicacion = ?, envio_gratis = ?, estatus = ?
                           WHERE id_publicacion = ?""",
                        (nuevo_precio, nuevo_stock, nuevo_tipo, int(nuevo_envio), nuevo_est, id_u),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Publicación actualizada.")
                    st.rerun()

    # --- DELETE PUBLICACIÓN ---
    with col_d:
        st.subheader("🗑️ Eliminar Publicación")
        if not df_pub.empty:
            opciones_d = {f"{r['ID']} - {r['Título']}": r["ID"] for _, r in df_pub.iterrows()}
            sel_d = st.selectbox("Publicación a borrar", list(opciones_d.keys()))
            id_d = opciones_d[sel_d]

            st.caption("Nota: SQLite bloqueará el borrado si la publicación ya tiene ventas registradas en `detalle_pedido`.")
            if st.button("Eliminar Publicación", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM publicaciones WHERE id_publicacion = ?", (id_d,))
                    con.commit()
                    st.cache_data.clear()
                    st.success("Publicación eliminada.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: existen pedidos asociados a esta publicación.")

    con.close()


# =====================================================================
# PESTAÑA 2: CRUD DE VENDEDORES (TABLA `usuarios`)
# =====================================================================
with tab_vend:
    con = get_connection("mercado_libre")

    st.subheader("Directorio de Vendedores y Reputación")
    df_vend_full = pd.read_sql(
        """
        SELECT u.id_usuario AS ID,
               u.nickname AS Nickname,
               u.nombre AS Nombre,
               u.apellidos AS Apellidos,
               u.correo AS Correo,
               COALESCE(u.telefono, '') AS Teléfono,
               u.tipo_usuario AS Rol,
               u.reputacion AS Reputación,
               CASE WHEN u.activo = 1 THEN 'Activo' ELSE 'Inactivo' END AS Estado,
               COUNT(DISTINCT p.id_publicacion) AS Publicaciones,
               COALESCE(SUM(dp.cantidad), 0) AS Unidades_Vendidas
        FROM usuarios u
        LEFT JOIN publicaciones p ON u.id_usuario = p.id_vendedor
        LEFT JOIN detalle_pedido dp ON p.id_publicacion = dp.id_publicacion
        WHERE u.tipo_usuario IN ('vendedor', 'ambos')
        GROUP BY u.id_usuario
        ORDER BY u.reputacion DESC
        """,
        con,
    )
    st.dataframe(df_vend_full, use_container_width=True, hide_index=True)

    st.divider()
    col_vc, col_vu, col_vd = st.columns(3)

    # --- CREATE VENDEDOR ---
    with col_vc:
        st.subheader("➕ Nuevo Vendedor")
        with st.form("form_crear_vendedor", clear_on_submit=True):
            v_nick = st.text_input("Nickname único*")
            v_nom = st.text_input("Nombre*")
            v_ape = st.text_input("Apellidos*")
            v_correo = st.text_input("Correo electrónico*")
            v_tel = st.text_input("Teléfono")
            v_rol = st.selectbox("Tipo de cuenta", ["vendedor", "ambos"])
            v_rep = st.slider("Reputación inicial (0.0 - 5.0)", 0.0, 5.0, 4.5, step=0.1)
            v_activo = st.checkbox("Cuenta activa", value=True)

            if st.form_submit_button("Registrar Vendedor", use_container_width=True):
                if not v_nick.strip() or not v_nom.strip() or not v_ape.strip() or not v_correo.strip():
                    st.error("Nickname, nombre, apellidos y correo son obligatorios.")
                else:
                    try:
                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO usuarios 
                               (nickname, nombre, apellidos, correo, telefono, contrasena_hash, tipo_usuario, reputacion, activo)
                               VALUES (?, ?, ?, ?, ?, 'hash_demo', ?, ?, ?)""",
                            (
                                v_nick.strip().upper(),
                                v_nom.strip(),
                                v_ape.strip(),
                                v_correo.strip(),
                                v_tel.strip(),
                                v_rol,
                                v_rep,
                                int(v_activo),
                            ),
                        )
                        con.commit()
                        st.success("Vendedor registrado.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El nickname o correo ya existe en la base de datos.")

    # --- UPDATE VENDEDOR ---
    with col_vu:
        st.subheader("✏️ Editar Reputación / Datos")
        if not df_vend_full.empty:
            opc_v = {f"{r['ID']} - {r['Nickname']}": r["ID"] for _, r in df_vend_full.iterrows()}
            sel_v = st.selectbox("Selecciona vendedor", list(opc_v.keys()))
            id_v_edit = opc_v[sel_v]
            vend_act = df_vend_full[df_vend_full["ID"] == id_v_edit].iloc[0]

            with st.form("form_editar_vendedor"):
                edit_v_tel = st.text_input("Teléfono", value=vend_act["Teléfono"])
                roles = ["vendedor", "ambos"]
                idx_r = roles.index(vend_act["Rol"]) if vend_act["Rol"] in roles else 0
                edit_v_rol = st.selectbox("Tipo de cuenta", roles, index=idx_r)
                edit_v_rep = st.slider(
                    "Reputación (0.0 - 5.0)", 0.0, 5.0, float(vend_act["Reputación"]), step=0.1
                )
                edit_v_act = st.checkbox("Cuenta activa", value=(vend_act["Estado"] == "Activo"))

                if st.form_submit_button("Actualizar Vendedor", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        """UPDATE usuarios 
                           SET telefono = ?, tipo_usuario = ?, reputacion = ?, activo = ?
                           WHERE id_usuario = ?""",
                        (edit_v_tel.strip(), edit_v_rol, edit_v_rep, int(edit_v_act), id_v_edit),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Vendedor actualizado (reputación sincronizada con el modelo ML).")
                    st.rerun()

    # --- DELETE VENDEDOR ---
    with col_vd:
        st.subheader("🗑️ Eliminar Vendedor")
        if not df_vend_full.empty:
            opc_vdel = {f"{r['ID']} - {r['Nickname']}": r["ID"] for _, r in df_vend_full.iterrows()}
            sel_vdel = st.selectbox("Vendedor a eliminar", list(opc_vdel.keys()))
            id_v_del = opc_vdel[sel_vdel]

            st.caption("Nota: SQLite bloqueará el borrado si el vendedor tiene publicaciones registradas.")
            if st.button("Eliminar Vendedor", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM usuarios WHERE id_usuario = ?", (id_v_del,))
                    con.commit()
                    st.cache_data.clear()
                    st.success("Vendedor eliminado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: este vendedor aún tiene publicaciones vinculadas.")

    con.close()


# =====================================================================
# PESTAÑA 3: MODELO PREDICTIVO CON EXPLICABILIDAD (REGRESIÓN)
# =====================================================================
with tab_pred:
    st.subheader("Simulador de Demanda Estimada por Publicación")
    st.write(
        "Entrena un regresor **Random Forest** con publicaciones vendidas y sin ventas registradas."
    )

    @st.cache_data
    def cargar_dataset_ml():
        con = get_connection("mercado_libre")
        query = """
            SELECT p.precio,
                   p.condicion,
                   p.tipo_publicacion,
                   p.envio_gratis,
                   u.reputacion,
                   COALESCE(SUM(dp.cantidad), 0) AS unidades_vendidas
            FROM publicaciones p
            JOIN usuarios u ON p.id_vendedor = u.id_usuario
            LEFT JOIN detalle_pedido dp ON p.id_publicacion = dp.id_publicacion
            GROUP BY p.id_publicacion
        """
        df = pd.read_sql(query, con)
        con.close()
        return df

    df_ml = cargar_dataset_ml()

    if len(df_ml) < 4:
        st.warning("Se necesitan al menos 4 publicaciones con ventas registradas para entrenar el modelo de regresión.")
    else:
        le_cond = LabelEncoder()
        le_tipo = LabelEncoder()

        df_ml["condicion_cod"] = le_cond.fit_transform(df_ml["condicion"])
        df_ml["tipo_cod"] = le_tipo.fit_transform(df_ml["tipo_publicacion"])

        features = ["precio", "condicion_cod", "tipo_cod", "envio_gratis", "reputacion"]
        X = df_ml[features]
        y = df_ml["unidades_vendidas"]

        modelo = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        modelo.fit(X, y)

        col_sim, col_res = st.columns(2)
        with col_sim, st.container(border=True):
            st.markdown("#### Parámetros de la Nueva Publicación")
            in_precio = st.number_input("Precio del producto ($ MXN)", min_value=50.0, value=799.0, step=50.0)
            in_cond = st.selectbox("Condición del artículo", le_cond.classes_)
            in_tipo = st.selectbox("Exposición (Tipo de publicación)", le_tipo.classes_)
            in_envio = st.checkbox("Incluye Envío Gratis", value=True)
            in_rep = st.slider("Reputación del vendedor (0.0 a 5.0)", 0.0, 5.0, 4.8, step=0.1)

            btn_predecir = st.button("Estimar Volumen de Ventas", type="primary", use_container_width=True)

        with col_res, st.container(border=True):
            st.markdown("#### Proyección de Ventas")
            if btn_predecir:
                X_nuevo = pd.DataFrame(
                    [[
                        in_precio,
                        le_cond.transform([in_cond])[0],
                        le_tipo.transform([in_tipo])[0],
                        int(in_envio),
                        in_rep,
                    ]],
                    columns=features,
                )
                pred_unidades = modelo.predict(X_nuevo)[0]
                ingreso_estimado = pred_unidades * in_precio

                st.metric("Demanda Estimada", f"{pred_unidades:.1f} unidades")
                st.metric("Ingreso Bruto Proyectado", f"${ingreso_estimado:,.2f} MXN")

                if in_tipo == "premium" and in_envio:
                    st.success("✅ Configuración óptima: máxima exposición + envío gratis impulsan la conversión.")
                elif not in_envio:
                    st.info("💡 Tip: Activar el envío gratis suele incrementar el volumen estimado en productos nuevos.")

        st.divider()
        exp1, exp2 = st.columns(2)

        with exp1:
            st.markdown("#### Importancia de Variables en el Modelo")
            df_imp = pd.DataFrame(
                {
                    "Variable": ["Precio", "Condición", "Tipo Publicación", "Envío Gratis", "Reputación Vendedor"],
                    "Importancia": modelo.feature_importances_,
                }
            ).set_index("Variable")
            st.bar_chart(df_imp, height=230)

        with exp2:
            st.markdown("#### Desempeño Histórico por Tipo y Envío")
            resumen_hist = (
                df_ml.groupby(["tipo_publicacion", "envio_gratis"])["unidades_vendidas"]
                .agg(Publicaciones="count", Promedio_Unidades="mean")
                .reset_index()
            )
            resumen_hist["envio_gratis"] = resumen_hist["envio_gratis"].map({1: "Sí", 0: "No"})
            resumen_hist["Promedio_Unidades"] = resumen_hist["Promedio_Unidades"].round(1)
            st.dataframe(resumen_hist, use_container_width=True, hide_index=True)