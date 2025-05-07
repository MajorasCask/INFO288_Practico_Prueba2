from flask import Flask, request
import json
import requests

app = Flask(__name__)

# Diccionario de URLs de esclavos
slaves = {}
with open("config.json") as config_file:
    config = json.load(config_file)
    for slave in config["slaves"]:
        slaves[slave["database"]] = f'http://{slave["ip"]}:{slave["port"]}'

# Funciones de ordenamiento de resultados
#
# Retorna ranking de elemento
def get_rank(json_elem):
    return json_elem["ranking"]
#
# Retorna interes del grupo etario de elemento
def get_interest(json_elem):
    return json_elem["interes"]

# Ruta de busqueda por palabra clave
# Retorno:
# {
#    "respuesta": [
#        {
#            "categoria": string,
#            "interes": int,
#            "ranking": int,
#            "tipo": string,
#            "titulo": string
#        }
#    ]
# }
@app.route("/buscar", methods=["GET"])
def busca_slave():

    #Lista comun de resultados
    responses = {"respuesta": []}
    
    # Lista de terminos de busqueda, error si no hay ninguno
    if "titulo" in request.args:
        wordlist = request.args["titulo"].replace(" ", "+")
    else: 
        return "Error, no especifica ningun termino de busqueda"

    # Edad, 0 si no se especifica (campo "interes" retorna null)
    if "edad" in request.args:
        age = request.args["edad"]
    else:
        age = "0"
    
    # Llamada a esclavos, espera el timeout a los no desplegados
    for slave in slaves:
        try:
            response = requests.get(f"{slaves[slave]}/busqueda?titulo={wordlist}&edad={age}")
        except:
            continue

        # Si respuesta es exitosa, agrega resultados a lista comun
        if response.status_code == 200:
            parse = json.loads(response.text)
            for entry in parse:
                responses["respuesta"].append(entry)
    
    # Ordena los resultados por ranking e interes por edad, donde el interes tiene preferencia
    responses["respuesta"].sort(key = lambda elem: (get_interest(elem), get_rank(elem)), reverse = True)
    
    return responses


# Ruta de busqueda por tipo de documento
# Retorno:
# {
#    <nombre-base-datos>: [
#        {
#            "tipo": string,
#            "titulo": string
#        }
#    ]
# }
@app.route("/filtrar", methods=["GET"])
def filtrar():

    responses = {}

    # Lista de tipos de documento, error si no hay ninguno
    if "tipo" in request.args:
        typelist = request.args["tipo"].split(" ")
    else: 
        return "Error, no especifica ningun tipo de documento"
    
    # Revisa si existen los tipos de documento, llama a esclavo si existen en cada caso, error si no
    slave_list = list(slaves.keys())
    for type in typelist:
        if type in slave_list:
            response = requests.get(f'{slaves[type]}/fetch_all')
        else:
            return f"Error, tipo de documento {type} no encontrado"
        
        # Si respuesta es exitosa, crea lista del tipo y agrega los resultados
        if response.status_code == 200:
            responses[type] = []
            parse = json.loads(response.text)
            for entry in parse:
                responses[type].append(entry)

    return responses

# Correr app en red local y puerto 5000
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)