import streamlit as st
from sqlalchemy import text
import time

conn = st.connection("db_prueba", type="sql")

st.set_page_config(
    page_title="Actualizar Reporte",
    page_icon="./logo.png",
    initial_sidebar_state="collapsed",
    layout="wide"
)

def query_segura(conn,sql,ttl=30,params=None,reintentos=2,espera=2):
    for intento in range(reintentos + 1):
        try:
            return conn.query(sql, ttl=ttl, params=params)
        except Exception:
            if intento < reintentos:
                time.sleep(espera)
                continue
        st.warning("La base de datos está despertando. Recarga la página en unos segundos")
        st.stop()

st.header("Actualizar Reporte")
folio = st.number_input("Folio del reporte", min_value=1, step=1, format="%d")

if st.button("Buscar"):
    st.session_state["folio_actual"] = folio

if "folio_actual" in st.session_state:
    fila = query_segura(conn,"""
        SELECT r.*, e.nombre AS estado_actual
        FROM core.reporte r LEFT JOIN catalogo.estado_procedimiento e ON e.id = r.estado_id
        WHERE r.id = :id
    """, params={"id": st.session_state["folio_actual"]}, ttl=0)

    if fila.empty:
        st.error(f"No existe el folio {st.session_state['folio_actual']}.")
    else:
        f = fila.iloc[0]
        st.success(f"Folio {f['id']} — estado actual: {f['estado_actual']}")
        st.caption(f["descripcion"])

        radiooperadores = query_segura(conn,"SELECT nombre FROM catalogo.radiooperador ORDER BY nombre", ttl=300)
        moviles = query_segura(conn,"SELECT codigo FROM catalogo.movil ORDER BY codigo", ttl=300)
        inspectores = query_segura(conn,"SELECT nombre FROM catalogo.inspector ORDER BY nombre", ttl=300)

        st.subheader("Asignación")
        c1, c2, c3 = st.columns(3)
        radiooperador = c1.selectbox("Radiooperador", radiooperadores["nombre"])
        movil = c2.selectbox("Móvil", moviles["codigo"])
        inspector = c3.selectbox("Inspector", inspectores["nombre"])

        b1, b2, b3 = st.columns(3)
        for label, campo, col in [("asignación", "hora_asignacion", b1), ("arribo", "hora_arribo", b2), ("término", "hora_termino", b3)]:
            if col.button(f"Marcar hora de {label} ahora"):
                with conn.session as s:
                    s.execute(text(f"UPDATE core.reporte SET {campo} = now() WHERE id = :id"), dict(id=int(f["id"])))
                    s.commit()
                st.cache_data.clear(); st.rerun()
        st.caption(f"Asignación: {f['hora_asignacion']} · Arribo: {f['hora_arribo']} · Término: {f['hora_termino']}")

        finalizaciones = query_segura(conn,"SELECT nombre FROM catalogo.finalizacion ORDER BY nombre", ttl=300)
        apoyos = query_segura(conn,"SELECT nombre FROM catalogo.apoyo_asistencia ORDER BY nombre", ttl=300)

        with st.form("form_cierre"):
            st.subheader("Cierre")
            apoyo_asistencia = st.selectbox("Apoyo/asistencia", apoyos["nombre"])
            finalizacion = st.selectbox("Finalización", finalizaciones["nombre"])
            informe = st.text_area("Informe", value=f["informe"] or "", height=200)
            observaciones = st.text_area("Observaciones", value=f["observaciones"] or "")
            connotacion = st.text_input("Connotación", value=f["connotacion"] or "")
            guardar = st.form_submit_button("Guardar cierre")

        if guardar:
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
                        actualizado_por = 'app_streamlit', actualizado_en = now()
                    WHERE id = :id AND actualizado_en IS NOT DISTINCT FROM :previo
                """), dict(radiooperador=radiooperador, movil=movil, inspector=inspector,
                           apoyo_asistencia=apoyo_asistencia, finalizacion=finalizacion,
                           informe=informe, observaciones=observaciones, connotacion=connotacion,
                           id=int(f["id"]), previo=f["actualizado_en"]))
                if resultado.rowcount == 0:
                    st.error("Alguien más modificó este reporte mientras tanto. Vuelve a buscarlo.")
                    s.rollback()
                else:
                    s.commit()
                    st.success("Reporte actualizado.")
                    del st.session_state["folio_actual"]
                    st.cache_data.clear()

    