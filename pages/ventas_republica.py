import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from conexion import get_connection

st.set_page_config(page_title="Ventas República | CRUD & Predicciones", page_icon="🇲🇽", layout="wide")


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
        (1, "Alejandro", "Garza", "a.garza@empresa.mx", "vendedor", "2025-01-15"),
        (2, "Beatriz", "Soto", "b.soto@empresa.mx", "vendedor", "2025-03-10"),
        (3, "César", "Vázquez", "c.vazquez@empresa.mx", "gerente", "2024-11-01"),
        (4, "Diana", "Pech", "d.pech@empresa.mx", "vendedor", "2025-06-20"),
    ]
    cur.executemany(
        "INSERT INTO empleados (id_sucursal, nombre, apellidos, correo, puesto, fecha_contratacion) VALUES (?, ?, ?, ?, ?, ?)",
        empleados,
    )

    # 3. Categorías y Productos
    cur.execute("INSERT INTO categorias (nombre) VALUES ('Equipamiento Industrial')")
    productos = [
        ("SKU-001", "Taladro Percutor 1/2 Pulgada", 1, 1850.0, 1100.0),
        ("SKU-002", "Juego de Llaves Mixtas 14 Pzas", 1, 650.0, 380.0),
        ("SKU-003", "Compresor de Aire 25L", 1, 3400.0, 2150.0),
    ]
    cur.executemany(
        "INSERT INTO productos (sku, nombre, id_categoria, precio_unitario, costo) VALUES (?, ?, ?, ?, ?)",
        productos,
    )

    # 4. Ventas históricas y Detalles (distintas zonas, meses, métodos y cantidades)
    ventas = [
        ("VTA-1001", 1, 1, "2026-03-12 10:30:00", "tarjeta_credito", 9250.0, 1480.0, 10730.0, "completada"),
        ("VTA-1002", 2, 2, "2026-04-18 14:15:00", "transferencia", 13600.0, 2176.0, 15776.0, "completada"),
        ("VTA-1003", 3, 3, "2026-05-22 11:00:00", "tarjeta_debito", 3900.0, 624.0, 4524.0, "completada"),
        ("VTA-1004", 4, 4, "2026-06-05 16:45:00", "efectivo", 1950.0, 312.0, 2262.0, "completada"),
        ("VTA-1005", 1, 1, "2026-08-14 12:20:00", "transferencia", 17000.0, 2720.0, 19720.0, "completada"),
        ("VTA-1006", 2, 2, "2026-09-25 17:10:00", "tarjeta_credito", 7400.0, 1184.0, 8584.0, "completada"),
        ("VTA-1007", 3, 3, "2026-10-09 09:50:00", "efectivo", 2600.0, 416.0, 3016.0, "completada"),
        ("VTA-1008", 4, 4, "2026-11-11 15:30:00", "tarjeta_debito", 5550.0, 888.0, 6438.0, "completada"),
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
    ]
    cur.executemany(
        "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento) VALUES (?, ?, ?, ?, ?)",
        detalles,
    )

    con.commit()
    con.close()


inicializar_datos_demo()

st.title("🇲🇽 Ventas a Nivel República: CRUD y Proyección de Ingresos")
tab_crud, tab_pred = st.tabs(["📋 CRUD de Ventas", "🤖 Predicción de Monto de Venta (ML)"])

# ---------------------------------------------------------------------
# PESTAÑA 1: CRUD DE VENTAS (CON DETALLE EN CASCADA)
# ---------------------------------------------------------------------
with tab_crud:
    con = get_connection("ventas_nivel_republica")
    df_suc = pd.read_sql(
        """SELECT s.id_sucursal, s.nombre || ' (' || z.nombre || ')' AS sucursal
           FROM sucursales s
           JOIN estados e ON s.id_estado = e.id_estado
           JOIN zonas z ON e.id_zona = z.id_zona""",
        con,
    )
    df_emp = pd.read_sql("SELECT id_empleado, nombre || ' ' || apellidos AS empleado FROM empleados", con)
    df_prod = pd.read_sql("SELECT id_producto, nombre, precio_unitario FROM productos", con)

    st.subheader("Registro Histórico de Ventas")
    df_ventas = pd.read_sql(
        """
        SELECT v.id_venta AS ID,
               v.folio AS Folio,
               z.nombre AS Zona,
               s.nombre AS Sucursal,
               v.fecha_venta AS Fecha,
               v.metodo_pago AS Método_Pago,
               COALESCE(SUM(dv.cantidad), 0) AS Artículos,
               v.total AS Total_MXN,
               v.estatus AS Estatus
        FROM ventas v
        JOIN sucursales s ON v.id_sucursal = s.id_sucursal
        JOIN estados e ON s.id_estado = e.id_estado
        JOIN zonas z ON e.id_zona = z.id_zona
        LEFT JOIN detalle_venta dv ON v.id_venta = dv.id_venta
        GROUP BY v.id_venta
        ORDER BY v.id_venta DESC
        """,
        con,
    )
    st.dataframe(df_ventas, use_container_width=True, hide_index=True)

    st.divider()
    col_c, col_u, col_d = st.columns(3)

    with col_c:
        st.subheader("➕ Registrar Venta")
        with st.form("form_crear_venta", clear_on_submit=True):
            folio = st.text_input("Folio único*", value=f"VTA-{1009 + len(df_ventas)}")
            suc_sel = st.selectbox("Sucursal", df_suc["sucursal"])
            emp_sel = st.selectbox("Vendedor", df_emp["empleado"])
            prod_sel = st.selectbox("Producto vendido", df_prod["nombre"])
            cantidad = st.number_input("Cantidad de unidades", min_value=1, value=2, step=1)
            metodo = st.selectbox("Método de pago", ["efectivo", "tarjeta_credito", "tarjeta_debito", "transferencia"])
            fecha_input = st.date_input("Fecha de venta", value=datetime.now())

            if st.form_submit_button("Guardar Ticket de Venta", use_container_width=True):
                if not folio.strip():
                    st.error("El folio es obligatorio.")
                else:
                    try:
                        id_suc = int(df_suc.loc[df_suc["sucursal"] == suc_sel, "id_sucursal"].values[0])
                        id_emp = int(df_emp.loc[df_emp["empleado"] == emp_sel, "id_empleado"].values[0])
                        fila_prod = df_prod[df_prod["nombre"] == prod_sel].iloc[0]
                        id_prod = int(fila_prod["id_producto"])
                        precio_u = float(fila_prod["precio_unitario"])

                        subtotal = precio_u * cantidad
                        iva = round(subtotal * 0.16, 2)
                        total = round(subtotal + iva, 2)
                        fecha_str = f"{fecha_input.strftime('%Y-%m-%d')} 12:00:00"

                        cur = con.cursor()
                        cur.execute(
                            """INSERT INTO ventas 
                               (folio, id_sucursal, id_empleado, fecha_venta, metodo_pago, subtotal, iva, total, estatus)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completada')""",
                            (folio.strip(), id_suc, id_emp, fecha_str, metodo, subtotal, iva, total),
                        )
                        id_nueva_venta = cur.lastrowid
                        cur.execute(
                            """INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, descuento)
                               VALUES (?, ?, ?, ?, 0)""",
                            (id_nueva_venta, id_prod, cantidad, precio_u),
                        )
                        con.commit()
                        st.cache_data.clear()
                        st.success(f"Venta {folio} registrada por ${total:,.2f} MXN.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("El folio ya existe. Usa un folio único.")

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

# ---------------------------------------------------------------------
# PESTAÑA 2: MODELO PREDICTIVO (PROYECCIÓN DE TOTAL DE VENTA)
# ---------------------------------------------------------------------
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
        with col_sim:
            st.markdown("#### Parámetros de la Operación")
            in_zona = st.selectbox("Zona geográfica de la República", le_zona.classes_)
            in_metodo = st.selectbox("Método de pago esperado", le_metodo.classes_)
            in_cant = st.slider("Cantidad de artículos en el pedido", 1, 20, 4)
            in_mes = st.slider("Mes del año (1 = Ene, 12 = Dic)", 1, 12, 11)

            btn_predecir = st.button("Proyectar Monto de Venta", type="primary", use_container_width=True)

        with col_res:
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

                with st.expander("Ver registros históricos usados para entrenar"):
                    st.dataframe(
                        df_ml[["zona", "metodo_pago", "total_articulos", "mes", "total"]],
                        use_container_width=True,
                    )