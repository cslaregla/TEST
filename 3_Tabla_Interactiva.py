from datetime import datetime
import streamlit as st
import pandas as pd

## Configuración inicial aplicación ##
st.set_page_config(page_title="Tabla Interactiva", layout="wide")
st.logo("./logo.png",size='large',icon_image="./logo.png")
st.title("🗃️ Tablas Reportes Central Ñuñoa 2026")

## Validación por seguridad ##
from auth import check_auth
if not check_auth():
    st.stop()

## Título y botones en una fila ##
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    if st.button("Inicio", key="nav_home", width='stretch'):
        st.switch_page("app.py")

with col2:
    if st.button("Mapa Interactivo", key="nav_mapa", width='stretch'):
        st.switch_page("pages/1_Mapa_Interactivo.py")

with col3:
    if st.button("Dashboard", key="nav_dash", width='stretch'):
        st.switch_page("pages/2_Dashboard.py")

with col4:
    if st.button("Tabla Interactiva", key="nav_tabla", width='stretch', type="primary"):
        st.switch_page("pages/3_Tabla_Interactiva.py")

with col5:
    if st.button("Exportar Reportes", key="nav_report", width='stretch'):
        st.switch_page("pages/4_Exportar_Reportes.py")

with col6:
    if st.button("Comparador Períodos", key='nav_comp', width='stretch'):
        st.switch_page("pages/5_Graficas_Comparativas.py")
st.markdown("---")
## Información sobre la data comprendida en la aplicación ##
dfr = pd.read_csv('info.csv', sep=';', engine='python')
dfr['FECHA Y HORA'] = pd.to_datetime(dfr['FECHA Y HORA'])
first_hist = dfr.iloc[0]['FECHA Y HORA']
last_hist = dfr.iloc[-1]['FECHA Y HORA']
st.markdown(f"Información integrada desde **{first_hist}** a **{last_hist}**")


## Enlisto los filtros ##
st.subheader("Filtros")
op_ingreso = ['1445', 'EXTERNO','INTERNO','JEFATURA','OPERADOR CÁMARAS','PROALERT','SOSAFE','OTROS', 'VECINO/A']
op_cuadrantes = ['Nro. 118','Nro. 119','Nro. 120','Nro. 121','Nro. 129','Nro. 130','Nro. 131','Nro. 132','Nro. 133','No aplica']
dop_categoria ={'Seguridad':['Servicio DRONE','Apoyo a Carabineros','Actividad sospechosa','Agresión','Alarma activada','Amenazas','Artefacto explosivo o paquete sospechoso','Daños propiedad privada','Daños propiedad pública','Delito sexual','Detención ciudadana','Detenidos','Disparos','Disturbios','Fuegos artificiales','Homicidio','Homicidio Frustrado','Hurto','Maltrato animal','Marchas/manifestaciones','Persona extraviada / desorientada','Posible sospechoso al interior','Riña','Robo con intimidación','Robo con violencia','Robo de especies de o desde vehículo','Robo de vehículo en BNUP','Robo en BNUP','Robo en lugar habitado','Robo en lugar no habitado','Robo frustrado','Robo por sorpresa','Toma establecimiento educacional','Trafico Drogas','Vehículo con encargo','Vehiculo sospechoso','Incumplimiento medida cautelar','VIF','Vulneración derechos adultos mayores','Vulneración NNA','Otros','Motochorros '],
                 'Planes Operativos':['7X3 delitos violentos','Control de Transito','Operativo Conjunto a otras Municipalidades','Operativo Conjunto Carabineros','Operativo conjunto Delegación Presidencial','Operativo conjunto Dirección de Inspección','Operativo MTT','Operativo otras direcciones Municilapales','Operativo Seremi Salud','Operativos Conjunto PDI','P.V.P','Patrulla Mixta','Patrullaje focalizado Carabineros','Patrullaje focalizado Preventivo','Patrullaje preventivo general','Punto fijo','Ruta calle','Servicio especial Colegios','Servicio Estadio','Servicio FEI','Servicio turístico Plaza Ñuñoa-Barrio Italia','Vigilancia especial','Otros'],
                 'Emergencia/Espacio Públicos':['Apoyo a Bomberos','Apoyo a SAMU','Accidente de tránsito (choque/colisión/atropello)','Acera en mal estado','Alcantarilla colapsada','Anegamiento de calle y paso bajo nivel','Anegamiento domicilios','Suicidio/Intento','Cables a baja altura / Cables cortados','Caida de arbol','Circuito y luminarias dañadas','Corte energía eléctrica','Corte suministro de agua potable','Desganche arbolado','Emanación de gas/ Derrame o Materiales peligrosos','Emergencia de salud','Filtración agua potable','Incendio o amago','Mascota atrapada/perdida','Pavimento en mal estado','Posible Fallecido/Emergencia de Salud','Postes dañados','Semáforo defectuoso','Señalética o elemento caida','Tapa de servicios','Otra contingencia BNUP','Otros'],
                 'Fiscalización':['Realizacion de Graffitis / Pintar sin autorización','Comercio ambulante Ilegal','Fiscalización alcoholes','Fiscalización aparcadores ilegales','Fiscalización de tránsito','Vehiculo MAL Estacionado','Vehículo sospechoso','Fiscalización ingesta de alcohol en vía pública','Fiscalizacion Retiro de circulación de vehiculo motorizado','Fiscalizacion Ruidos Molestos','Fiscalizaciones (BNUP, comercio, etc)','Trabajos fuera de horario','Vehículo abandonado','Otros'],
                 'Incivilidades':['Botar chicle, colillas o desechos en la vía pública','Carpa o Ruco en BNUP','Consumo de alcohol en vía pública','Consumo de drogas','Ebriedad','Microbasural','Persona situación de calle','Otros'],
                 'Otros':['Novedades Central','Labores administrativas','Traslado de documentos o funcionarios/limpieza de móvil','Otros']}
op_categoria = list(dop_categoria.keys())
op_tipo =['Servicio DRONE','Apoyo a Carabineros','Actividad sospechosa','Agresión','Alarma activada','Amenazas','Artefacto explosivo o paquete sospechoso','Daños propiedad privada','Daños propiedad pública','Delito sexual','Detención ciudadana','Detenidos','Disparos','Disturbios','Fuegos artificiales','Homicidio','Homicidio Frustrado','Hurto','Maltrato animal','Marchas/manifestaciones','Persona extraviada / desorientada','Posible sospechoso al interior','Riña','Robo con intimidación','Robo con violencia','Robo de especies de o desde vehículo','Robo de vehículo en BNUP','Robo en BNUP','Robo en lugar habitado','Robo en lugar no habitado','Robo frustrado','Robo por sorpresa','Toma establecimiento educacional','Trafico Drogas','Vehículo con encargo','Vehiculo sospechoso','Incumplimiento medida cautelar','VIF','Vulneración derechos adultos mayores','Vulneración NNA','Otros','Motochorros ','7X3 delitos violentos','Control de Transito','Operativo Conjunto a otras Municipalidades','Operativo Conjunto Carabineros','Operativo conjunto Delegación Presidencial','Operativo conjunto Dirección de Inspección','Operativo MTT','Operativo otras direcciones Municilapales','Operativo Seremi Salud','Operativos Conjunto PDI','P.V.P','Patrulla Mixta','Patrullaje focalizado Carabineros','Patrullaje focalizado Preventivo','Patrullaje preventivo general','Punto fijo','Ruta calle','Servicio especial Colegios','Servicio Estadio','Servicio FEI','Servicio turístico Plaza Ñuñoa-Barrio Italia','Vigilancia especial','Otros','Apoyo a Bomberos','Apoyo a SAMU','Accidente de tránsito (choque/colisión/atropello)','Acera en mal estado','Alcantarilla colapsada','Anegamiento de calle y paso bajo nivel','Anegamiento domicilios','Suicidio/Intento','Cables a baja altura / Cables cortados','Caida de arbol','Circuito y luminarias dañadas','Corte energía eléctrica','Corte suministro de agua potable','Desganche arbolado','Emanación de gas/ Derrame o Materiales peligrosos','Emergencia de salud','Filtración agua potable','Incendio o amago','Mascota atrapada/perdida','Pavimento en mal estado','Posible Fallecido/Emergencia de Salud','Postes dañados','Semáforo defectuoso','Señalética o elemento caida','Tapa de servicios','Otra contingencia BNUP','Otros','Realizacion de Graffitis / Pintar sin autorización','Comercio ambulante Ilegal','Fiscalización alcoholes','Fiscalización aparcadores ilegales','Fiscalización de tránsito','Vehiculo MAL Estacionado','Vehículo sospechoso','Fiscalización ingesta de alcohol en vía pública','Fiscalizacion Retiro de circulación de vehiculo motorizado','Fiscalizacion Ruidos Molestos','Fiscalizaciones (BNUP, comercio, etc)','Trabajos fuera de horario','Vehículo abandonado','Otros','Botar chicle, colillas o desechos en la vía pública','Carpa o Ruco en BNUP','Consumo de alcohol en vía pública','Consumo de drogas','Ebriedad','Microbasural','Persona situación de calle','Otros','Novedades Central','Labores administrativas','Traslado de documentos o funcionarios/limpieza de móvil','Otros','Patrullaje preventivo', 'Focalizado municipal', 'Fiscalización conjunta (Carabineros, PDI)', 'Operativos conjuntos: colaboración con Carabineros, PDI', 'Fiscalización', 'Ruidos Molestos', 'Retiro de enseres de la via publica', 'Seguridad (prevención)', 'Seguridad']
op_hinicio = {0:'00:00',1:'01:00',2:'02:00',3:'03:00',4:'04:00',5:'05:00',6:'06:00',7:'07:00',8:'08:00',9:'09:00',10:'10:00',11:'11:00',12:'12:00',13:'13:00',14:'14:00',15:'15:00',16:'16:00',17:'17:00',18:'18:00',19:'19:00',20:'20:00',21:'21:00',22:'22:00',23:'23:00',24:'24:00'}
op_hfinal = {0:'00:00',1:'01:00',2:'02:00',3:'03:00',4:'04:00',5:'05:00',6:'06:00',7:'07:00',8:'08:00',9:'09:00',10:'10:00',11:'11:00',12:'12:00',13:'13:00',14:'14:00',15:'15:00',16:'16:00',17:'17:00',18:'18:00',19:'19:00',20:'20:00',21:'21:00',22:'22:00',23:'23:00', 24:'24:00'}
op_mes = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
op_ano = [2020,2021,2022,2023,2024,2025,2026]
op_comisaria = ['33° Comisaría','18° Comisaría','No hubo','NO APLICA']
opi_hinicio = list(op_hinicio.items())
opi_hfinal = list(op_hfinal.items())
opi_mes = list(op_mes.items())
col1, col2, col3, col4, col5 = st.columns(5)
col6, col7, col8, col9, col10 = st.columns(5)
with col1:
    ingreso = st.multiselect("Vía de Ingreso", op_ingreso,placeholder='Elige')
with col2:
    cuadrante = st.multiselect("Cuadrante", op_cuadrantes, placeholder='Elige')
with col3:
    categoria = st.selectbox("Categoría", op_categoria, index=None,placeholder='Elige')
with col4:
    if categoria:
        ltipo = dop_categoria[categoria]
        tipo = st.multiselect("Tipo", ltipo,placeholder='Elige')
    else:
        tipo = st.multiselect("Tipo", op_tipo,placeholder='Elige')
with col5:
    shinicio = st.selectbox("Hora Inicio",options=opi_hinicio,format_func=lambda o: o[1], index=None, placeholder='Elige')
    if shinicio:
        hinicio = shinicio[0]
    else:
        hinicio = None
with col6:
    shfinal = st.selectbox("Hora Final",options=opi_hfinal,format_func=lambda o: o[1], index=None, placeholder='Elige')
    if shfinal:
        hfinal = shfinal[0]
    else:
        hfinal = None
with col7:
    smes = st.selectbox("Mes",options=opi_mes,format_func=lambda o: o[1], index=None, placeholder='Elige')
    if smes:
        mes = smes[0]
    else:
        mes = None
with col8:
    ano = st.selectbox("Año", op_ano, index=None,placeholder='Elige')
with col9:
    finicio = st.date_input("Desde", value=None)
with col10:
    ffinal = st.date_input("Hasta", value=None)
col11, col12, col13, col14, col15 = st.columns(5)
with col11:
    calle = st.text_input("Calle",'',placeholder="Elige")
with col12:
    numeracion = st.text_input("Numeración",'',placeholder="Elige")
with col13:
    palabra = st.text_input("Palabra Clave",'',placeholder="Elige")
with col14:
    comisaria = st.selectbox("Comisaría", op_comisaria, index=None,placeholder='Elige')

## Cargo el archivo .csv ##
df = pd.read_csv('info.csv', sep=';', engine='python')
df_filtrado = df.copy()
df_filtrado['FECHA Y HORA'] = pd.to_datetime(df_filtrado['FECHA Y HORA'])

## Filtro la base de datos ##
if ingreso:
    df_filtrado = df_filtrado[df_filtrado['CANAL DE INGRESO'].isin(ingreso)]
if cuadrante:
     df_filtrado = df_filtrado[df_filtrado['CUADRANTE'].isin(cuadrante)]
if categoria:
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA'] == categoria]
if tipo:
    df_filtrado = df_filtrado[df_filtrado['TIPO DE PROCEDIMIENTO'].isin(tipo)]
if mes:
    df_filtrado = df_filtrado[df_filtrado['FECHA Y HORA'].dt.month == mes]
if ano:
    df_filtrado = df_filtrado[df_filtrado['FECHA Y HORA'].dt.year == ano]
if hinicio and hfinal and hinicio > hfinal:
    df_filtrado = df_filtrado[(df_filtrado['FECHA Y HORA'].dt.hour >= hinicio) | (df_filtrado['FECHA Y HORA'].dt.hour < hfinal)]
if hinicio and hfinal and hinicio < hfinal:
    df_filtrado = df_filtrado[(df_filtrado['FECHA Y HORA'].dt.hour >= hinicio) & (df_filtrado['FECHA Y HORA'].dt.hour < hfinal)]
if hinicio and not hfinal:
    df_filtrado = df_filtrado[df_filtrado['FECHA Y HORA'].dt.hour >= hinicio]
if hfinal and not hinicio:
    df_filtrado = df_filtrado[df_filtrado['FECHA Y HORA'].dt.hour < hfinal]
if finicio:
    df_filtrado = df_filtrado[df_filtrado['FECHA Y HORA'].dt.date >= finicio]
if ffinal:
    df_filtrado = df_filtrado[df_filtrado['FECHA Y HORA'].dt.date <= ffinal]
if calle:
    df_filtrado = df_filtrado[df_filtrado['CALLE'].str.contains(calle, case=False, na=False) | df_filtrado['CALLE QUE INTERSECTA'].str.contains(calle, case=False, na=False)]
if numeracion:
    df_filtrado = df_filtrado[df_filtrado['NUMERACIÓN'].str.contains(numeracion, case=False, na=False)]
if palabra:
    df_filtrado = df_filtrado[df_filtrado['INFORME'].str.contains(palabra, case=False, na=False) | df_filtrado['DESCRIPCION DEL PROCEDIMIENTO (DETALLES RELEVANTES)'].str.contains(palabra, case=False, na=False)]
if comisaria:
    df_filtrado = df_filtrado[df_filtrado['COMISARIA'] == comisaria]

## RESALTAR ##
def highlight(val):
    if palabra and palabra.lower() in str(val).lower():
        return "background-color: yellow"
    return ""


## Muestro el resultado en una tabla ##
st.subheader("Resultados")
st.write(f"Total de registros: {len(df_filtrado)}")
#st.dataframe(df_filtrado[df_filtrado.columns[2:26]], width='stretch')
#st.dataframe(df_estilado,width='stretch')

## PAGINACION ##
#entradas_por_pagina = st.selectbox("Por página:", [10, 25, 50, 100])
entradas_por_pagina = 100
pagina = st.number_input("Página:", 1, max(1, (len(df_filtrado) // entradas_por_pagina) + 1))
inicio = (pagina - 1) * entradas_por_pagina
fin = inicio + entradas_por_pagina
if palabra:
    df_estilado = df_filtrado.iloc[inicio:fin].style.map(highlight)
    st.dataframe(df_estilado, width='stretch')
if not palabra:
    df_estilado = df_filtrado
    st.dataframe(df_estilado.iloc[inicio:fin], width='stretch')
st.write(f"Página {pagina} de {(len(df_filtrado) // entradas_por_pagina) + 1}")