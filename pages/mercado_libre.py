import sqlite3
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection

st.set_page_config(page_title="Mercado Libre | CRUD & Predicciones", page_icon="🛒", layout="wide")


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
        ("TECH_STORE_MX", "Ricardo", "Salinas", "ventas@techstore.mx", "5510001001", "hash1", "vendedor", 4.9),
        ("GADGETS_EXPRESS", "Mónica", "Núñez", "monica@gadgets.mx", "5510001002", "hash2", "vendedor", 4.2),
        ("BAZAR_USADOS", "Tomás", "Aguilar", "tomas@bazar.mx", "5510001003", "hash3", "vendedor", 3.1),
        ("COMPRADOR_01", "Paola", "Ríos", "paola@mail.com", "5510001004", "hash4", "comprador", 5.0),
        ("COMPRADOR_02", "Fernando", "Lara", "fer@mail.com", "5510001005", "hash5", "comprador", 4.8),
    ]
    cur.executemany(
        """INSERT INTO usuarios (nickname, nombre, apellidos, correo, telefono, contrasena_hash, tipo_usuario, reputacion)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
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

    # 5. Pedidos y Detalle de Pedidos (patrón: premium + envío gratis + alta reputación = más ventas)
    pedidos = [
        (4, 1, "entregado", 4495.0),
        (5, 1, "entregado", 3294.0),
        (4, 1, "pagado", 2598.0),
        (5, 1, "entregado", 1260.0),
        (4, 1, "entregado", 560.0),
        (5, 1, "entregado", 1650.0),
        (4, 1, "pagado", 4200.0),
        (5, 1, "entregado", 950.0),
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

st.title("🛒 Mercado Libre: CRUD de Publicaciones y Predicción de Demanda")
tab_crud, tab_pred = st.tabs(["📋 CRUD de Publicaciones", "🤖 Predicción de Unidades Vendidas (ML)"])

# ---------------------------------------------------------------------
# PESTAÑA 1: CRUD DE PUBLICACIONES
# ---------------------------------------------------------------------
with tab_crud:
    con = get_connection("mercado_libre")
    df_vendedores = pd.read_sql(
        "SELECT id_usuario, nickname || ' (Rep: ' || reputacion || ')' AS vendedor FROM usuarios WHERE tipo_usuario IN ('vendedor','ambos')",
        con,
    )
    df_categorias = pd.read_sql("SELECT id_categoria, nombre FROM categorias", con)

    st.subheader("Catálogo de Publicaciones Activas")
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
               p.estatus AS Estatus
        FROM publicaciones p
        JOIN usuarios u ON p.id_vendedor = u.id_usuario
        JOIN categorias c ON p.id_categoria = c.id_categoria
        ORDER BY p.id_publicacion DESC
        """,
        con,
    )
    st.dataframe(df_pub, use_container_width=True, hide_index=True)

    st.divider()
    col_c, col_u, col_d = st.columns(3)

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

# ---------------------------------------------------------------------
# PESTAÑA 2: MODELO PREDICTIVO (REGRESIÓN DE UNIDADES VENDIDAS)
# ---------------------------------------------------------------------
with tab_pred:
    st.subheader("Simulador de Demanda Estimada por Publicación")
    st.write(
        "Entrena un regresor **Random Forest** cruzando `publicaciones`, `usuarios` y `detalle_pedido` "
        "para estimar cuántas unidades se venderán según la configuración del anuncio."
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
        st.warning("Se necesitan al menos 4 publicaciones registradas para entrenar el modelo de regresión.")
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
        with col_sim:
            st.markdown("#### Parámetros de la Nueva Publicación")
            in_precio = st.number_input("Precio del producto ($ MXN)", min_value=50.0, value=799.0, step=50.0)
            in_cond = st.selectbox("Condición del artículo", le_cond.classes_)
            in_tipo = st.selectbox("Exposición (Tipo de publicación)", le_tipo.classes_)
            in_envio = st.checkbox("Incluye Envío Gratis", value=True)
            in_rep = st.slider("Reputación del vendedor (0.0 a 5.0)", 0.0, 5.0, 4.8, step=0.1)

            btn_predecir = st.button("Estimar Volumen de Ventas", type="primary", use_container_width=True)

        with col_res:
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

                with st.expander("Ver matriz histórica de entrenamiento"):
                    st.dataframe(
                        df_ml[["precio", "condicion", "tipo_publicacion", "envio_gratis", "reputacion", "unidades_vendidas"]],
                        use_container_width=True,
                    )

