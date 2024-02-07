from geopy.geocoders import Nominatim
from flask import Flask, render_template, request
from aemet import Aemet, Estacion
import pandas as pd
import os
import functions 

### AEMET INFORMACION ###
my_key = 'SUBSTITUYE_POR_LLAVE_AEMET'
aemet = Aemet(api_key = my_key)
#########################

app = Flask(__name__)   

@app.route('/')
def show_form():
    return render_template('main/formulario_localizacion.html')

@app.route('/localizacion-form', methods=['POST'])
def localizacion_form():
    # Formulario
    municipio = request.form['input_municipio']
    provincia = request.form['input_provincia']

    return render_template('main/formulario_usuario.html', result=[municipio, provincia])

@app.route('/usuario-form', methods=['POST'])
def usuario_form():
    
    
    municipio = request.form['input_municipio']
    provincia = request.form['input_provincia']
    tipo_hogar = request.form['input_tipo_hogar']
    altura_hogar = request.form['input_altura_hogar']
    jardin = request.form['input_jardin']
    balcon = request.form['input_balcon']
    consumo = request.form['input_consumo']
    mantenimiento = request.form['input_mantenimiento']

    data_sesion = {}

    data_sesion["municipio"] = municipio
    data_sesion["provincia"] = provincia
    data_sesion["tipo_hogar"] = tipo_hogar
    data_sesion["altura_hogar"] = altura_hogar
    data_sesion["jardin"] = jardin
    data_sesion["balcon"] = balcon
    data_sesion["consumo"] = consumo
    data_sesion["mantenimiento"] = mantenimiento
    
    predicciones = functions.processing_user_info(data_sesion)
    return render_template("main/resultados.html", result = predicciones)

if __name__ == '__main__':
    app.run(debug=True)