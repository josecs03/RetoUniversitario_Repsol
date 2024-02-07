from geopy.geocoders import Nominatim
from aemet import Aemet, Estacion
import joblib
import math
import pandas as pd
import os
import sklearn
from sklearn.ensemble import RandomForestClassifier
import numpy as np
###################### AEMET ######################

### AEMET INFORMACION ###
my_key = 'SUBSTITUYE_POR_LLAVE_AEMET'
aemet = Aemet(api_key = my_key)
#########################

# Función para calcular la distancia euclidiana en un espacio bidimensional
def distancia_euclidiana(lat1, lon1, lat2, lon2):
    dx = lat2 - lat1
    dy = lon2 - lon1
    distancia = math.sqrt(dx**2 + dy**2)
    return distancia

# Función para encontrar el id más cercano
def encontrar_id_mas_cercano(df, lat, lon):
    df['distancia'] = df.apply(lambda row: distancia_euclidiana(lat, lon, row['latitud'], row['longitud']), axis=1)
    id_mas_cercano = df['id'][df['distancia'].idxmin()]
    nombre_mas_cercano = df['nombre'][df['distancia'].idxmin()]
    distancia_minima = df['distancia'].min()
    return id_mas_cercano, nombre_mas_cercano, distancia_minima

# Función para transformar las ubicaciones dadas a coordenadas
def transformar_a_coordenadas(municipio, provincia):
    # Llamando a la librería
    geolocalizador = Nominatim(user_agent="my_geocoder")

    # Obtener coordenadas a partir de una dirección
    direccion = str(municipio + "," + provincia)
    ubicacion = geolocalizador.geocode(direccion, exactly_one=True)
    # Asumimos que siempre hay un resultado correcto
    #### LATITUD ####
    latitud = ubicacion.latitude
    latitud = str(latitud)
    latitud = latitud[:latitud.find(".")+5]
    latitud = latitud.replace('.', '')
    latitud = int(latitud)
    #### LONGITUD ####
    longitud = ubicacion.longitude
    longitud = str(longitud)
    longitud = longitud[:longitud.find(".")+5]
    longitud = longitud.replace('.', '')
    longitud = int(longitud)


    return latitud, longitud

# Función para procesar y guardar los datos de la estación para el procesamiento del modelo
def datos_estacion(id_estacion):

    datos = aemet.get_valores_climatologicos_mensuales(2023, id_estacion)
    # Meses frios: 1,2,10,11,12,13
    # Meses cálidos: 3,4,5,6,7,8,9
    datos_finales_estacion = []

    # Incializamos estructura datos vacia, a 0 para luego ir sumando (y más tarde hacer la media) 12 variables por 2 (frio, calor)
    for i in range(24): 
        datos_finales_estacion.append(0)
    
    # Vemos si estamos en un mes frio o calido y adjuntamos (sumando) los datos de ese mes
    for i in range(len(datos)-1):
        idx = datos[i]["fecha"][-2:]
        if ((idx == "-1") or (idx =="-2") or (idx == "10") or (idx=="11") or (idx=="12") or (idx=="13")):
            number = 0
        
        else: 
            number = 12
        
        # IMPORTANTE PARA EL MODELO: los nombres dan igual, lo importante es que los datos de los meses fríos vayan primero
        datos_finales_estacion[0 + number] += float(datos[i]["tm_mes"]) #temperatura_media
        datos_finales_estacion[1 + number] += float(datos[i]["w_med"]) #velocidad_viento_media
        datos_finales_estacion[2 + number] += float(datos[i]["p_mes"]) #precipitacion_media
        datos_finales_estacion[3 + number] += float(datos[i]["n_cub"]) #dias_nubosidad
        datos_finales_estacion[4 + number] += float(datos[i]["hr"]) #humedad_relativa
        datos_finales_estacion[5 + number] += float(datos[i]["n_gra"]) #numero_dias_granizo
        datos_finales_estacion[6 + number] += float(datos[i]["n_fog"]) #numero_dias_niebla
        datos_finales_estacion[7 + number] += float(datos[i]["nt_00"]) #numero_dias_menos_0_grados
        datos_finales_estacion[8 + number] += float(datos[i]["n_tor"]) #numero_dias_tornados
        datos_finales_estacion[9 + number] += float(datos[i]["n_nie"]) #numero_dias_nieve  
        datos_finales_estacion[10 + number] += float(datos[i]["p_sol"]) #horas_sol
        datos_finales_estacion[11 + number] += float(datos[i]["glo"]) #radiacion_solar  
    # Para hacer la media, dividimos la suma de cada variable entre los meses que hemos considerado.
    for i in range(len(datos_finales_estacion)):
        if i <= 11:
            datos_finales_estacion[i] /= 6
        else:
            datos_finales_estacion[i] /= 7
            
    return  datos_finales_estacion

# Función para aplicar el modelo       
def aplicar_modelo(datos_usuario, modelo_path):
    datos_usuario = np.array([datos_usuario])
    modelo = joblib.load(modelo_path)

    #datos_usuario = datos_usuario.values.reshape(1, -1)

    nuevas_predicciones = modelo.predict(datos_usuario)
    return(nuevas_predicciones)
    


# Función principal que se llama desde el main y devuelve la predicción
def processing_user_info(data_sesion):

    # A) Ubicacion -> coordenadas
    # print(data_sesion)
    latitud, longitud = transformar_a_coordenadas(data_sesion["municipio"], data_sesion["provincia"])
    # B) Encontrar estacion mas cercana
    # 1. Obtener la ruta completa al archivo CSV en la carpeta "static"
    csv_path = os.path.join('static', 'estaciones_coordenadas.csv')
    # 2. Cargar el CSV en un DataFrame de pandas
    estaciones_coordenadas = pd.read_csv(csv_path)
    # 3. Llamar a la función
    id_estacion, nombre_estacion, distancia_estacion = encontrar_id_mas_cercano(estaciones_coordenadas, latitud, longitud)
    # C) Sacar los datos de la estación (solo los necesarios)
    datos_para_modelo = datos_estacion(id_estacion)

    # D) Unir los datos de la estación y del usuario
    datos_para_modelo.append(data_sesion["tipo_hogar"])
    datos_para_modelo.append(data_sesion["altura_hogar"])
    datos_para_modelo.append(data_sesion["jardin"])
    datos_para_modelo.append(data_sesion["balcon"])
    datos_para_modelo.append(data_sesion["consumo"])
    datos_para_modelo.append(data_sesion["mantenimiento"])


    datos_para_modelo = [float(element) for element in datos_para_modelo]


    # E) Aplicar el modelo
    predicciones = aplicar_modelo(datos_para_modelo, os.path.join("models", "modelo_random_forest2.joblib"))
    # El output es una lista con una lista, nos quedamos con lo de dentro
    predicciones = predicciones[0]
    # Son floats de 0.0 o 1.0 -> lo pasamos a integer
    predicciones = [int(element) for element in predicciones]
 
    return predicciones
