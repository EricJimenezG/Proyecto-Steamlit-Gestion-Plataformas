import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection
from datos_demo import agregar_registros_demo
from interfaz import render_kpi_cards, render_page_header, render_sidebar

st.set_page_config(page_title="Ventas República | Predicciones", page_icon="🇲🇽", layout="wide")
render_sidebar("Ventas República", "Gestiona ventas y productos, y proyecta los montos de venta.")


# =====================================================================
# 1. POBLADO INICIAL DE DATOS (Solo si la BD está vacía)
# =====================================================================
def inicializar_datos_demo():
    con = get_connection("ventas_nivel_republica")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM zonas")
    if cur.fetchone()[0] > 0:
        con.close()
        return

    # 1. Zonas y Estados
    zonas = [("Norte",), ("Centro",), ("Bajío",), ("Sur",)]
    cur.executemany("INSERT INTO zonas (nombre) VALUES (?)", zonas)

    estados = [
        ("NL", "Nuevo León", 1),
        ("MEX", "Estado de México", 2),
        ("GTO", "Guanajuato", 3),
        ("YUC", "Yucatán", 4),
    ]
    cur.executemany("INSERT INTO estados (clave, nombre, id_zona) VALUES (?, ?, ?)", estados)

    # 2. Sucursales y Empleados
    sucursales = [
        ("Sucursal Monterrey Centro", 1, "Monterrey", "Av. Constitución 400"),
        ("Sucursal Cuautitlán Izcalli", 2, "Cuautitlán Izcalli", "Av. Primero de Mayo 105"),
        ("Sucursal León Plaza", 3, "León", "Blvd. Adolfo López Mateos 810"),
        ("Sucursal Mérida Norte", 4, "Mérida", "Prolongación Montejo 220"),
    ]
    cur.executemany(
        "INSERT INTO sucursales (nombre, id_estado, ciudad, direccion) VALUES (?, ?, ?, ?)",
        sucursales,
    )

    empleados = [
        (1, "Alejandro", "Garza", "a.garza@empresa.mx", "vendedor", "2025-01-15", 1),
        (2, "Beatriz", "Soto", "b.soto@empresa.mx", "vendedor", "2025-03-10", 1),
        (3, "César", "Vázquez", "c.vazquez@empresa.mx", "gerente", "2024-11-01", 1),
        (4, "Diana", "Pech", "d.pech@empresa.mx", "vendedor", "2025-06-20", 1),
    ]
    cur.executemany(
        """INSERT INTO empleados (id_sucursal, nombre, apellidos, correo, puesto, fecha_contratacion, activo) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        empleados,
    )

    # 3. Categorías y Productos
    categorias = [("Herramienta Eléctrica",), ("Herramienta Manual",), ("Equipos Neumáticos",)]
    cur.executemany("INSERT INTO categorias (nombre) VALUES (?)", categorias)

    productos = [
        ("SKU-001", "Taladro Percutor 1/2 Pulgada", 1, 1850.0, 1100.0, 1),
        ("SKU-002", "Juego de Llaves Mixtas 14 Pzas", 2, 650.0, 380.0, 1),
        ("SKU-003", "Compresor de Aire 25L", 3, 3400.0, 2150.0, 1),
        ("SKU-004", "Esmeriladora Angular 4-1/2", 1, 1250.0, 740.0, 1),
    ]
    cur.executemany(
        "INSERT INTO productos (sku, nombre, id_categoria, precio_unitario, costo, activo) VALUES (?, ?, ?, ?, ?, ?)",
        productos,
    )

    # 4. Ventas históricas y Detalles (12 tickets distribuidos en las 4 zonas y distintos meses)
    ventas = [
        ("VTA-1001", 1, 1, "2026-02-12 10:30:00", "tarjeta_credito", 9250.0, 1480.0, 10730.0, "completada"),
        ("VTA-1002", 2, 2, "2026-03-18 14:15:00", "transferencia", 13600.0, 2176.0, 15776.0, "completada"),
        ("VTA-1003", 3, 3, "2026-04-22 11:00:00", "tarjeta_debito", 3900.0, 624.0, 4524.0, "completada"),
        ("VTA-1004", 4, 4, "2026-05-05 16:45:00", "efectivo", 1950.0, 312.0, 2262.0, "completada"),
        ("VTA-1005", 1, 1, "2026-06-14 12:20:00", "transferencia", 17000.0, 2720.0, 19720.0, "completada"),
        ("VTA-1006", 2, 2, "2026-07-25 17:10:00", "tarjeta_credito", 7400.0, 1184.0, 8584.0, "completada"),
        ("VTA-1007", 3, 3, "2026-08-09 09:50:00", "efectivo", 2600.0, 416.0, 3016.0, "completada"),
        ("VTA-1008", 4, 4, "2026-09-11 15:30:00", "tarjeta_debito", 5550.0, 888.0, 6438.0, "completada"),
        ("VTA-1009", 1, 1, "2026-10-03 11:40:00", "transferencia", 20400.0, 3264.0, 23664.0, "completada"),
        ("VTA-1010", 2, 2, "2026-10-21 13:15:00", "tarjeta_credito", 11100.0, 1776.0, 12876.0, "completada"),
        ("VTA-1011", 3, 3, "2026-11-04 10:05:00", "tarjeta_debito", 6250.0, 1000.0, 7250.0, "completada"),
        ("VTA-1012", 4, 4, "2026-11-15 18:20:00", "efectivo", 3750.0, 600.0, 4350.0, "completada"),
    ]
    cur.executemany(
        """INSERT INTO ventas 
           (folio, id_sucursal, id_empleado, fecha_venta, metodo_pago, subtotal, iva, total, estatus)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ventas,
    )

    detalles = [
        (1, 1, 5, 1850.0, 0),
        (2, 3, 4, 3400.0, 0),
        (3, 2, 6, 650.0, 0),
        (4, 2, 3, 650.0, 0),
        (5, 3, 5, 3400.0, 0),
        (6, 1, 4, 1850.0, 0),
        (7, 2, 4, 650.0, 0),
        (8, 1, 3, 1850.0, 0),
        (9, 3, 6, 3400.0, 0),
        (10, 1, 6, 1850.0, 0),
        (11, 4, 5, 1250.0, 0),
        (12, 4, 3, 1250.0, 0),
    ]
    cur.executemany(
        "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento) VALUES (?, ?, ?, ?, ?)",
        detalles,
    )

    con.commit()
    con.close()


inicializar_datos_demo()
if agregar_registros_demo("ventas_nivel_republica"):
    st.cache_data.clear()

render_page_header(
    "🇲🇽 Ventas a Nivel República",
    "Explora el desempeño comercial por región y proyecta montos de venta.",
)

tab_ventas, tab_productos, tab_pred = st.tabs(
    ["📋 Ventas", "📦 Productos", "🤖 Predicción de Monto de Venta"]
)

# =====================================================================
# PESTAÑA 1: CRUD DE VENTAS + KPIs + GRÁFICAS + EXPORTACIÓN CSV
# =====================================================================
with tab_ventas:
    con = get_connection("ventas_nivel_republica")

    df_suc = pd.read_sql(
        """SELECT s.id_sucursal, s.nombre || ' (' || z.nombre || ')' AS sucursal
           FROM sucursales s
           JOIN estados e ON s.id_estado = e.id_estado
           JOIN zonas z ON e.id_zona = z.id_zona
           WHERE s.activa = 1""",
        con,
    )
    df_emp = pd.read_sql(
        "SELECT id_empleado, nombre || ' ' || apellidos AS empleado FROM empleados WHERE activo = 1", con
    )
    df_prod = pd.read_sql(
        "SELECT id_producto, sku || ' - ' || nombre AS prod_label, precio_unitario FROM productos WHERE activo = 1",
        con,
    )

    df_ventas = pd.read_sql(
        """
        SELECT v.id_venta AS ID,
               v.folio AS Folio,
               z.nombre AS Zona,
               s.nombre AS Sucursal,
               e_v.nombre || ' ' || e_v.apellidos AS Vendedor,
               v.fecha_venta AS Fecha,
               v.metodo_pago AS Método_Pago,
               COALESCE(SUM(dv.cantidad), 0) AS Artículos,
               v.subtotal AS Subtotal,
               v.iva AS IVA,
               v.total AS Total_MXN,
               v.estatus AS Estatus
        FROM ventas v
        JOIN sucursales s ON v.id_sucursal = s.id_sucursal
        JOIN estados est ON s.id_estado = est.id_estado
        JOIN zonas z ON est.id_zona = z.id_zona
        JOIN empleados e_v ON v.id_empleado = e_v.id_empleado
        LEFT JOIN detalle_venta dv ON v.id_venta = dv.id_venta
        GROUP BY v.id_venta
        ORDER BY v.id_venta DESC
        """,
        con,
    )

    # --- KPIs Ejecutivos ---
    df_comp = df_ventas[df_ventas["Estatus"] == "completada"] if not df_ventas.empty else pd.DataFrame()
    num_ventas = len(df_comp)
    ingresos_tot = float(df_comp["Total_MXN"].sum()) if not df_comp.empty else 0.0
    ticket_prom = float(df_comp["Total_MXN"].mean()) if not df_comp.empty else 0.0
    articulos_tot = int(df_comp["Artículos"].sum()) if not df_comp.empty else 0

    render_kpi_cards(
        [
            ("Ventas completadas", num_ventas),
            ("Ingresos totales", f"${ingresos_tot:,.2f}"),
            ("Ticket promedio", f"${ticket_prom:,.2f}"),
            ("Unidades despachadas", f"{articulos_tot} u."),
        ]
    )

    # --- Gráficas por Zona y Método de Pago ---
    if not df_comp.empty:
        g1, g2 = st.columns(2)
        with g1:
            with st.container(border=True):
                st.markdown("#### Ingresos por zona (MXN)")
                st.bar_chart(df_comp.groupby("Zona")["Total_MXN"].sum(), height=220)
        with g2:
            with st.container(border=True):
                st.markdown("#### Operaciones por método de pago")
                st.bar_chart(df_comp["Método_Pago"].value_counts(), height=220)

    # --- Tabla Principal (READ) + Descarga CSV ---
    st.subheader("Registro Histórico de Ventas")
    st.dataframe(df_ventas, use_container_width=True, hide_index=True)

    csv_ventas = df_ventas.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Exportar Reporte de Ventas a CSV",
        data=csv_ventas,
        file_name="reporte_ventas_republica.csv",
        mime="text/csv",
    )

    st.divider()
    col_c, col_u, col_d = st.columns(3)

    # --- CREATE VENTA ---
    with col_c:
        st.subheader("➕ Registrar Venta")
        with st.form("form_crear_venta", clear_on_submit=True):
            folio = st.text_input("Folio único*", value=f"VTA-{1001 + len(df_ventas)}")
            suc_sel = st.selectbox("Sucursal", df_suc["sucursal"])
            emp_sel = st.selectbox("Vendedor", df_emp["empleado"])
            prod_sel = st.selectbox("Producto vendido", df_prod["prod_label"])
            cantidad = st.number_input("Cantidad de unidades", min_value=1, value=3, step=1)
            metodo = st.selectbox("Método de pago", ["efectivo", "tarjeta_credito", "tarjeta_debito", "transferencia"])
            fecha_input = st.date_input("Fecha de venta", value=datetime.now())

            if st.form_submit_button("Guardar Ticket de Venta", use_container_width=True):
                if not folio.strip():
                    st.error("El folio es obligatorio.")
                elif df_prod.empty:
                    st.error("No hay productos activos disponibles.")
                else:
                    try:
                        id_suc = int(df_suc.loc[df_suc["sucursal"] == suc_sel, "id_sucursal"].values[0])
                        id_emp = int(df_emp.loc[df_emp["empleado"] == emp_sel, "id_empleado"].values[0])
                        fila_prod = df_prod[df_prod["prod_label"] == prod_sel].iloc[0]
                        id_prod = int(fila_prod["id_producto"])
                        precio_u = float(fila_prod["precio_unitario"])

                        subtotal = round(precio_u * cantidad, 2)
                        iva = round(subtotal * 0.16, 2)
                        total = round(subtotal + iva, 2)
                        fecha_str = f"{fecha_input.strftime('%Y-%m-%d')} 12:00:00"

                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO ventas 
                               (folio, id_sucursal, id_empleado, fecha_venta, metodo_pago, subtotal, iva, total, estatus)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completada')""",
                            (folio.strip().upper(), id_suc, id_emp, fecha_str, metodo, subtotal, iva, total),
                        )
                        id_nueva_venta = cur.lastrowid
                        cur.execute(
                            """INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento)
                               VALUES (?, ?, ?, ?, 0)""",
                            (id_nueva_venta, id_prod, cantidad, precio_u),
                        )
                        con.commit()
                        st.cache_data.clear()
                        st.success(f"Venta {folio.upper()} registrada por ${total:,.2f} MXN.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El folio ya existe. Usa un folio único.")

    # --- UPDATE VENTA ---
    with col_u:
        st.subheader("✏️ Actualizar Venta")
        if not df_ventas.empty:
            opciones_u = {f"{r['ID']} - {r['Folio']} (${r['Total_MXN']})": r["ID"] for _, r in df_ventas.iterrows()}
            sel_u = st.selectbox("Selecciona venta", list(opciones_u.keys()))
            id_u = opciones_u[sel_u]
            actual = df_ventas[df_ventas["ID"] == id_u].iloc[0]

            with st.form("form_edit_venta"):
                metodos = ["efectivo", "tarjeta_credito", "tarjeta_debito", "transferencia"]
                nuevo_met = st.selectbox("Método de pago", metodos, index=metodos.index(actual["Método_Pago"]))
                estados = ["completada", "cancelada", "devuelta"]
                nuevo_est = st.selectbox("Estatus", estados, index=estados.index(actual["Estatus"]))

                if st.form_submit_button("Actualizar Venta", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        "UPDATE ventas SET metodo_pago = ?, estatus = ? WHERE id_venta = ?",
                        (nuevo_met, nuevo_est, id_u),
                    )
                    con.commit()
                    st.cache_data.clear()
                    st.success("Venta actualizada.")
                    st.rerun()

    # --- DELETE VENTA ---
    with col_d:
        st.subheader("🗑️ Eliminar Venta")
        if not df_ventas.empty:
            opciones_d = {f"{r['ID']} - {r['Folio']}": r["ID"] for _, r in df_ventas.iterrows()}
            sel_d = st.selectbox("Venta a eliminar", list(opciones_d.keys()))
            id_d = opciones_d[sel_d]

            st.caption("Al eliminar una venta, su detalle se borra automáticamente (`ON DELETE CASCADE`).")
            if st.button("Eliminar Registro de Venta", type="primary", use_container_width=True):
                cur = con.cursor()
                cur.execute("DELETE FROM ventas WHERE id_venta = ?", (id_d,))
                con.commit()
                st.cache_data.clear()
                st.success("Venta eliminada.")
                st.rerun()

    con.close()


# =====================================================================
# PESTAÑA 2: CRUD DE PRODUCTOS (CATÁLOGO Y MÁRGENES)
# =====================================================================
with tab_productos:
    con = get_connection("ventas_nivel_republica")
    df_cats = pd.read_sql("SELECT id_categoria, nombre FROM categorias", con)

    st.subheader("Catálogo de Productos")
    df_productos = pd.read_sql(
        """
        SELECT p.id_producto AS ID,
               p.sku AS SKU,
               p.nombre AS Producto,
               c.nombre AS Categoría,
               p.precio_unitario AS Precio_Venta,
               p.costo AS Costo,
               ROUND(p.precio_unitario - p.costo, 2) AS Utilidad_Unitaria,
               CASE WHEN p.activo = 1 THEN 'Activo' ELSE 'Inactivo' END AS Estado,
               COALESCE(SUM(dv.cantidad), 0) AS Unidades_Vendidas
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        LEFT JOIN detalle_venta dv ON p.id_producto = dv.id_producto
        GROUP BY p.id_producto
        ORDER BY p.id_producto ASC
        """,
        con,
    )
    st.dataframe(df_productos, use_container_width=True, hide_index=True)

    st.divider()
    col_pc, col_pu, col_pd = st.columns(3)

    # --- CREATE PRODUCTO ---
    with col_pc:
        st.subheader("➕ Nuevo Producto")
        with st.form("form_crear_prod", clear_on_submit=True):
            p_sku = st.text_input("SKU único*", value=f"SKU-00{len(df_productos) + 1}")
            p_nom = st.text_input("Nombre del producto*")
            p_cat = st.selectbox("Categoría", df_cats["nombre"])
            p_precio = st.number_input("Precio unitario ($ MXN)", min_value=1.0, value=950.0, step=50.0)
            p_costo = st.number_input("Costo ($ MXN)", min_value=0.0, value=550.0, step=50.0)
            p_act = st.checkbox("Producto activo", value=True)

            if st.form_submit_button("Registrar Producto", use_container_width=True):
                if not p_sku.strip() or not p_nom.strip():
                    st.error("SKU y nombre son obligatorios.")
                else:
                    try:
                        id_cat = int(df_cats.loc[df_cats["nombre"] == p_cat, "id_categoria"].values[0])
                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO productos (sku, nombre, id_categoria, precio_unitario, costo, activo)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (p_sku.strip().upper(), p_nom.strip(), id_cat, p_precio, p_costo, int(p_act)),
                        )
                        con.commit()
                        st.success("Producto agregado al catálogo.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El SKU ya existe. Ingresa un código distinto.")

    # --- UPDATE PRODUCTO ---
    with col_pu:
        st.subheader("✏️ Editar Precios / Estado")
        if not df_productos.empty:
            opc_p = {f"{r['ID']} - {r['SKU']} ({r['Producto']})": r["ID"] for _, r in df_productos.iterrows()}
            sel_p = st.selectbox("Selecciona producto", list(opc_p.keys()))
            id_p_edit = opc_p[sel_p]
            prod_act = df_productos[df_productos["ID"] == id_p_edit].iloc[0]

            with st.form("form_editar_prod"):
                edit_precio = st.number_input(
                    "Precio de venta ($)", min_value=1.0, value=float(prod_act["Precio_Venta"]), step=50.0
                )
                edit_costo = st.number_input(
                    "Costo ($)", min_value=0.0, value=float(prod_act["Costo"]), step=50.0
                )
                edit_p_act = st.checkbox("Activo para venta", value=(prod_act["Estado"] == "Activo"))

                if st.form_submit_button("Guardar Cambios", use_container_width=True):
                    cur = con.cursor()
                    cur.execute(
                        "UPDATE productos SET precio_unitario = ?, costo = ?, activo = ? WHERE id_producto = ?",
                        (edit_precio, edit_costo, int(edit_p_act), id_p_edit),
                    )
                    con.commit()
                    st.success("Producto actualizado.")
                    st.rerun()

    # --- DELETE PRODUCTO ---
    with col_pd:
        st.subheader("🗑️ Eliminar Producto")
        if not df_productos.empty:
            opc_pdel = {f"{r['ID']} - {r['SKU']} ({r['Producto']})": r["ID"] for _, r in df_productos.iterrows()}
            sel_pdel = st.selectbox("Producto a eliminar", list(opc_pdel.keys()))
            id_p_del = opc_pdel[sel_pdel]

            st.caption("Nota: SQLite bloqueará el borrado si el producto ya forma parte de tickets vendidos.")
            if st.button("Eliminar Producto", type="primary", use_container_width=True):
                try:
                    cur = con.cursor()
                    cur.execute("DELETE FROM productos WHERE id_producto = ?", (id_p_del,))
                    con.commit()
                    st.success("Producto eliminado.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("No se puede eliminar: existen registros en `detalle_venta` vinculados a este producto.")

    con.close()


# =====================================================================
# PESTAÑA 3: MODELO PREDICTIVO CON EXPLICABILIDAD (REGRESIÓN)
# =====================================================================
with tab_pred:
    st.subheader("Simulador de Proyección de Ticket de Venta")
    st.write(
        "Entrena un regresor **Random Forest** utilizando `zonas`, `ventas` y `detalle_venta` "
        "para estimar el monto total de una operación comercial."
    )

    @st.cache_data
    def cargar_dataset_ml():
        con = get_connection("ventas_nivel_republica")
        query = """
            SELECT z.nombre AS zona,
                   v.metodo_pago,
                   CAST(strftime('%m', v.fecha_venta) AS INTEGER) AS mes,
                   COALESCE(SUM(dv.cantidad), 1) AS total_articulos,
                   v.total
            FROM ventas v
            JOIN sucursales s ON v.id_sucursal = s.id_sucursal
            JOIN estados e ON s.id_estado = e.id_estado
            JOIN zonas z ON e.id_zona = z.id_zona
            LEFT JOIN detalle_venta dv ON v.id_venta = dv.id_venta
            WHERE v.estatus = 'completada'
            GROUP BY v.id_venta
        """
        df = pd.read_sql(query, con)
        con.close()
        return df

    df_ml = cargar_dataset_ml()

    if len(df_ml) < 4:
        st.warning("Se requieren al menos 4 ventas con estatus 'completada' para entrenar el modelo.")
    else:
        le_zona = LabelEncoder()
        le_metodo = LabelEncoder()

        df_ml["zona_cod"] = le_zona.fit_transform(df_ml["zona"])
        df_ml["metodo_cod"] = le_metodo.fit_transform(df_ml["metodo_pago"])

        features = ["zona_cod", "metodo_cod", "total_articulos", "mes"]
        X = df_ml[features]
        y = df_ml["total"]

        modelo = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
        modelo.fit(X, y)

        col_sim, col_res = st.columns(2)
        with col_sim, st.container(border=True):
            st.markdown("#### Parámetros de la Operación")
            in_zona = st.selectbox("Zona geográfica de la República", le_zona.classes_)
            in_metodo = st.selectbox("Método de pago esperado", le_metodo.classes_)
            in_cant = st.slider("Cantidad de artículos en el pedido", 1, 20, 4)
            in_mes = st.slider("Mes del año (1 = Ene, 12 = Dic)", 1, 12, 11)

            btn_predecir = st.button("Proyectar Monto de Venta", type="primary", use_container_width=True)

        with col_res, st.container(border=True):
            st.markdown("#### Resultado de la Proyección")
            if btn_predecir:
                X_nuevo = pd.DataFrame(
                    [[
                        le_zona.transform([in_zona])[0],
                        le_metodo.transform([in_metodo])[0],
                        in_cant,
                        in_mes,
                    ]],
                    columns=features,
                )
                monto_predicho = modelo.predict(X_nuevo)[0]

                st.metric("Monto Total Estimado", f"${monto_predicho:,.2f} MXN")
                st.info(f"Proyección calculada para la zona **{in_zona}** con pago vía **{in_metodo}**.")

        st.divider()
        exp1, exp2 = st.columns(2)

        with exp1:
            st.markdown("#### Importancia de Variables en el Modelo")
            df_imp = pd.DataFrame(
                {
                    "Variable": ["Zona Geográfica", "Método de Pago", "Cantidad de Artículos", "Mes de Venta"],
                    "Importancia": modelo.feature_importances_,
                }
            ).set_index("Variable")
            st.bar_chart(df_imp, height=230)

        with exp2:
            st.markdown("#### Desempeño Histórico por Zona")
            resumen_zona = (
                df_ml.groupby("zona")["total"]
                .agg(Tickets="count", Ticket_Promedio="mean", Ingreso_Total="sum")
                .reset_index()
            )
            resumen_zona["Ticket_Promedio"] = resumen_zona["Ticket_Promedio"].round(2)
            resumen_zona["Ingreso_Total"] = resumen_zona["Ingreso_Total"].round(2)
            st.dataframe(resumen_zona, use_container_width=True, hide_index=True)

