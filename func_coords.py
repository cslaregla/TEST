import pandas as pd
from geopy.geocoders import ArcGIS

geolocator = ArcGIS(user_agent="geocoder_app")
def geocodificar(calle, numeracion, interseccion):

    calle = str(calle).strip() if pd.notna(calle) else ''
    numeracion = str(numeracion).strip() if pd.notna(numeracion) else ''
    interseccion = str(interseccion).strip() if pd.notna(interseccion) else ''
    
    # Caso 1: Hay intersección
    if calle and interseccion:
        direccion = f"{calle} & {interseccion}"
    
    # Caso 2: Hay numeración
    elif calle and numeracion:
        direccion = f"{calle} {numeracion}"
    
    # Caso 3: Solo calle
    elif calle and not numeracion and not interseccion:
        direccion = f"{calle}"
    print(direccion)
    comuna = 'Ñuñoa, Chile'
    try:
        if not direccion or direccion.strip() == '':
            return None,None
        
        ubicacion = geolocator.geocode(f"{direccion}, {comuna}", timeout=10)
        
        if ubicacion:
            # Retornar como tupla o string
            return ubicacion.latitude,ubicacion.longitude
        else:
            return None,None
    
    except Exception as e:
        print(f"Error: {e}")
        return None,None

calle = str(input('INGRESE CALLE: '))
numero = str(input('INGRESE NUMERO: '))
esq = str(input('INGRESE ESQ: '))
coords = geocodificar(calle,numero,esq)
print(coords)