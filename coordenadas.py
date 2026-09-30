from geopy.geocoders import ArcGIS
import pandas as pd
import re
import time


file = 'infoadd.csv'
df = pd.read_csv(file,sep=';',engine='python')
df['FECHA Y HORA'] = pd.to_datetime(df['FECHA Y HORA'])
df = df[['CALLE','NUMERACIÓN','CALLE QUE INTERSECTA']]
###
def extraer_numero(texto):
    """Extrae el primer número de un string"""
    if pd.isna(texto) or texto == '':
        return ''
    
    texto = str(texto).strip()
    match = re.search(r'\d+', texto)
    
    return match.group() if match else ''

def construir_direccion(calle, numeracion, interseccion):
    """
    Construye la dirección según los casos:
    - Si hay intersección: CALLE & CALLE QUE INTERSECTA
    - Si hay numeración con número: CALLE NÚMERO
    - Si solo calle: CALLE
    """
    calle = str(calle).strip() if pd.notna(calle) else ''
    numeracion = str(numeracion).strip() if pd.notna(numeracion) else ''
    interseccion = str(interseccion).strip() if pd.notna(interseccion) else ''
    
    # Caso 1: Hay intersección
    if calle and interseccion:
        return f"{calle} & {interseccion}"
    
    # Caso 2: Hay numeración
    if calle and numeracion:
        # Extraer solo el número
        numero = extraer_numero(numeracion)
        if numero:
            return f"{calle} {numero}"
        else:
            return calle
    
    # Caso 3: Solo calle
    if calle:
        return calle
    
    return ''

# Aplicar función
df['DIRECCION_LIMPIA'] = df.apply(
    lambda row: construir_direccion(
        row['CALLE'],
        row['NUMERACIÓN'],
        row['CALLE QUE INTERSECTA']
    ),
    axis=1
)


geolocator = ArcGIS(user_agent="geocoder_app")

def obtener_coordenadas(direccion, ciudad='Ñuñoa, Chile'):
    """Obtiene coordenadas de una dirección"""
    try:
        if not direccion or direccion.strip() == '':
            return None
        
        ubicacion = geolocator.geocode(f"{direccion}, {ciudad}", timeout=10)
        
        if ubicacion:
            # Retornar como tupla o string
            return f"{ubicacion.latitude},{ubicacion.longitude}"
        else:
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Aplicar función
print("Obteniendo coordenadas...")
coordenadas = []
a = 1
for idx, direccion in enumerate(df['DIRECCION_LIMPIA']):
    print(a)
    a+=1
    coord = obtener_coordenadas(direccion)
    coordenadas.append(coord)
    time.sleep(0.1)  # Importante: pausa entre solicitudes

df['COORDENADAS'] = coordenadas
df.to_csv('CALLES'+'P.csv', index=False,sep=';')
###
