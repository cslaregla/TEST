import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import date
import time

conn = st.connection("db_prueba", type="sql")

def query_segura(sql, ttl=30, params=None, reintentos=2, espera=2):
    for intento in range(reintentos + 1):
        try:
            return conn.query(sql, ttl=ttl, params=params)
        except Exception:
            if intento < reintentos:
                time.sleep(espera); continue
            st.warning("La base de datos está despertando. Recarga la página en unos segundos.")
            st.stop()

st.set_page_config(
    page_title="Actualizar Reporte",
    page_icon="./logo.png",
    initial_sidebar_state="collapsed",
    layout="wide"
)
st.header("🔄 Actualizar Reporte")

## Título y botones en una fila ##
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Nuevo Reporte", key="nav_new", width='stretch'):
        st.switch_page("app.py")

with col2:
    if st.button("Actualizar Reporte", key="nav_updt", width='stretch'):
        st.switch_page("pages/1_Actualizar_reporte.py")

with col3:
    if st.button("Visualización", key="nav_view", width='stretch'):
        st.switch_page("pages/2_Vista.py")

# =================================================================
# 1. BÚSQUEDA — guarda resultados en session_state, nunca en variable local
# =================================================================
st.subheader("Buscar reporte")
modo = st.radio("Buscar por", ["Folio", "Fecha y operador"], horizontal=True)

if modo == "Folio":
    folio = st.number_input("Folio", min_value=1, step=1, format="%d")
    if st.button("Buscar"):
        st.session_state["candidatos"] = query_segura("""
            SELECT r.id, r.fecha_hora, r.descripcion, c.nombre AS categoria
            FROM core.reporte r LEFT JOIN catalogo.categoria c ON c.id = r.categoria_id
            WHERE r.id = :v
        """, params={"v": folio}, ttl=0)
else:
    operadores = query_segura("SELECT nombre FROM catalogo.operador ORDER BY nombre", ttl=300)
    tipos = query_segura("SELECT nombre FROM catalogo.tipo_procedimiento ORDER BY nombre", ttl=300)
    fecha = st.date_input("Fecha", value=date.today())
    operador = st.selectbox("Operador", operadores["nombre"])
    tipo = st.selectbox("Tipo de procedimiento", ["Cualquiera"] + list(tipos["nombre"]))

    if st.button("Buscar"):
        condiciones = ["r.fecha_hora::date = :fecha", "o.nombre = :operador"]
        params = {"fecha": fecha, "operador": operador}
        if tipo != "Cualquiera":
            condiciones.append("tp.nombre = :tipo")
            params["tipo"] = tipo
        st.session_state["candidatos"] = query_segura(f"""
            SELECT r.id, r.fecha_hora, r.descripcion, c.nombre AS categoria
            FROM core.reporte r
            LEFT JOIN catalogo.operador o ON o.id = r.operador_id
            LEFT JOIN catalogo.categoria c ON c.id = r.categoria_id
            LEFT JOIN catalogo.tipo_procedimiento tp ON tp.id = r.tipo_procedimiento_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY r.fecha_hora DESC
        """, params=params, ttl=0)

if "candidatos" in st.session_state:
    candidatos = st.session_state["candidatos"]
    if candidatos.empty:
        st.warning("No se encontró ningún reporte con ese criterio.")
        del st.session_state["candidatos"]
    elif len(candidatos) == 1:
        st.session_state["folio_actual"] = int(candidatos.iloc[0]["id"])
        del st.session_state["candidatos"]
    else:
        st.info(f"Se encontraron {len(candidatos)} reportes, elige el correcto:")
        for _, r in candidatos.iterrows():
            hora = r["fecha_hora"].strftime("%H:%M") if pd.notna(r["fecha_hora"]) else "?"
            if st.button(f"{hora} — {r['categoria']} — {r['descripcion'][:50]}", key=f"sel_{r['id']}"):
                st.session_state["folio_actual"] = int(r["id"])
                del st.session_state["candidatos"]
                st.rerun()

# =================================================================
# 2. "FOTO CONGELADA" — se carga solo cuando cambia el folio, no en cada rerun
# =================================================================
if "folio_actual" in st.session_state:
    necesita_cargar = (
        "reporte_cargado" not in st.session_state
        or st.session_state["reporte_cargado"]["id"] != st.session_state["folio_actual"]
    )
    if necesita_cargar:
        fila = query_segura("SELECT * FROM core.reporte WHERE id = :id",
                             params={"id": st.session_state["folio_actual"]}, ttl=0)
        if fila.empty:
            st.error(f"No existe el folio {st.session_state['folio_actual']}.")
            del st.session_state["folio_actual"]
        else:
            st.session_state["reporte_cargado"] = fila.iloc[0].to_dict()

# =================================================================
# 3. FORMULARIO — siempre lee de la foto congelada, nunca re-consulta antes de guardar
# =================================================================
if "reporte_cargado" in st.session_state:
    f = st.session_state["reporte_cargado"]

    estado_actual = query_segura("SELECT nombre FROM catalogo.estado_procedimiento WHERE id = :id",
                                   params={"id": f["estado_id"]}, ttl=300)
    nombre_estado = estado_actual["nombre"].iloc[0] if not estado_actual.empty else "sin estado"
    st.success(f"Folio {f['id']} — estado actual: {nombre_estado}")
    st.caption(f["descripcion"])

    radiooperadores = query_segura("SELECT id, nombre FROM catalogo.radiooperador ORDER BY nombre", ttl=300)
    moviles = query_segura("SELECT id, codigo FROM catalogo.movil ORDER BY codigo", ttl=300)
    inspectores = query_segura("SELECT id, nombre FROM catalogo.inspector ORDER BY nombre", ttl=300)
    finalizaciones = query_segura("SELECT id, nombre FROM catalogo.finalizacion ORDER BY nombre", ttl=300)
    apoyos = query_segura("SELECT id, nombre FROM catalogo.apoyo_asistencia ORDER BY nombre", ttl=300)

    def opciones_con_actual(df, columna_valor, columna_id, valor_actual_id):
        opciones = ["— sin asignar —"] + list(df[columna_valor])
        if valor_actual_id is None:
            return opciones, 0
        coincidencias = df.index[df[columna_id] == valor_actual_id].tolist()
        return opciones, (coincidencias[0] + 1 if coincidencias else 0)

    st.subheader("Asignación")
    opciones_radio, idx_radio = opciones_con_actual(radiooperadores, "nombre", "id", f["radiooperador_id"])
    opciones_movil, idx_movil = opciones_con_actual(moviles, "codigo", "id", f["movil_id"])
    opciones_insp, idx_insp = opciones_con_actual(inspectores, "nombre", "id", f["inspector_id"])

    c1, c2, c3 = st.columns(3)
    radiooperador = c1.selectbox("Radiooperador", opciones_radio, index=idx_radio)
    movil = c2.selectbox("Móvil", opciones_movil, index=idx_movil)
    inspector = c3.selectbox("Inspector", opciones_insp, index=idx_insp)

    b1, b2, b3 = st.columns(3)
    for label, campo, col in [("asignación", "hora_asignacion", b1), ("arribo", "hora_arribo", b2), ("término", "hora_termino", b3)]:
        if col.button(f"Marcar hora de {label} ahora"):
            with conn.session as s:
                resultado = s.execute(text(f"""
                    UPDATE core.reporte SET {campo} = now(), actualizado_por = :quien, actualizado_en = now()
                    WHERE id = :id AND actualizado_en IS NOT DISTINCT FROM :previo
                    RETURNING *
                """), dict(id=f["id"], quien=radiooperador, previo=f["actualizado_en"]))
                fila_actualizada = resultado.mappings().first()
                if fila_actualizada is None:
                    st.error("Alguien más modificó este reporte mientras tanto. Vuelve a buscarlo.")
                    s.rollback()
                else:
                    s.commit()
                    st.session_state["reporte_cargado"] = dict(fila_actualizada)
            st.cache_data.clear()
            st.rerun()

    st.caption(f"Asignación: {f['hora_asignacion']} · Arribo: {f['hora_arribo']} · Término: {f['hora_termino']}")

    opciones_final, idx_final = opciones_con_actual(finalizaciones, "nombre", "id", f["finalizacion_id"])
    opciones_apoyo, idx_apoyo = opciones_con_actual(apoyos, "nombre", "id", f["apoyo_asistencia_id"])

    with st.form("form_cierre"):
        st.subheader("Cierre")
        apoyo_asistencia = st.selectbox("Apoyo/asistencia", opciones_apoyo, index=idx_apoyo)
        finalizacion = st.selectbox("Finalización", opciones_final, index=idx_final)
        informe = st.text_area("Informe", value=f["informe"] or "", height=200)
        observaciones = st.text_area("Observaciones", value=f["observaciones"] or "")
        connotacion = st.text_input("Connotación", value=f["connotacion"] or "")
        guardar = st.form_submit_button("Guardar cierre")

    if guardar:
        def o_nulo(v):
            return None if v == "— sin asignar —" else v

        with conn.session as s:
            resultado = s.execute(text("""
                UPDATE core.reporte SET
                    radiooperador_id = (SELECT id FROM catalogo.radiooperador WHERE nombre = :radiooperador),
                    movil_id = (SELECT id FROM catalogo.movil WHERE codigo = :movil),
                    inspector_id = (SELECT id FROM catalogo.inspector WHERE nombre = :inspector),
                    apoyo_asistencia_id = (SELECT id FROM catalogo.apoyo_asistencia WHERE nombre = :apoyo_asistencia),
                    finalizacion_id = (SELECT id FROM catalogo.finalizacion WHERE nombre = :finalizacion),
                    informe = :informe, observaciones = :observaciones, connotacion = :connotacion,
                    estado_id = (SELECT id FROM catalogo.estado_procedimiento WHERE nombre = 'Finalizado'),
                    actualizado_por = :quien, actualizado_en = now()
                WHERE id = :id AND actualizado_en IS NOT DISTINCT FROM :previo
            """), dict(
                radiooperador=o_nulo(radiooperador), movil=o_nulo(movil), inspector=o_nulo(inspector),
                apoyo_asistencia=o_nulo(apoyo_asistencia), finalizacion=o_nulo(finalizacion),
                informe=informe, observaciones=observaciones, connotacion=connotacion,
                quien=o_nulo(radiooperador) or "desconocido",
                id=f["id"], previo=f["actualizado_en"],
            ))
            if resultado.rowcount == 0:
                st.error("Alguien más modificó este reporte mientras tanto. Vuelve a buscarlo.")
                s.rollback()
            else:
                s.commit()
                st.success("Reporte actualizado.")
                del st.session_state["reporte_cargado"]
                del st.session_state["folio_actual"]
                st.cache_data.clear()
    