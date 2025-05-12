from flask import Flask, request
import json
import sys
import re
from collections import defaultdict
#imports de log
import time
import socket
from log_utils import build_log, log_local
from log_client import send_logs_to_server

app = Flask(__name__)

# Clase Slave
#
# dbname: Nombre de la DB
# config: archivo config.json
# port: puerto de despliegue
# database: Lista de elementos en la DB
# inv_index: Diccionario indice invertido
class Slave:
    def __init__(self, dbname):
        self.dbname = dbname

        with open('config.json') as config_file:
            self.config = json.load(config_file)
        
        # Carga base de datos segun nombre, Exception si no existe tal nombre
        for entry in self.config["slaves"]:
            if entry["database"] == dbname:
                self.port = entry["port"]
                with open(f'base_datos_slaves/{dbname}.json', encoding="utf8") as db_slave:
                    self.database = json.load(db_slave)[dbname]
                break
            elif self.config["slaves"][-1] == entry:
                raise Exception(f"Base de datos \"{entry['database']}\" no existe")
        
        # Diccionario para reemplazar tildes
        replacements = str.maketrans({"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"})

        # Palabras ignoradas en busquedas
        stopwords = [
            "a", "e", "o", "u", "y",
            "el", "la", "los", "las",
            "un", "una", "unos", "unas",
            "que", "con", "sin", "en", "como", "por", "para",
            "sobre", "su", "sus", "de", "del",
            "es", "son", "tu", "tus", "hacia"
        ]

        # Creacion indice invertido
        inverted_index = defaultdict(set)
        for element in self.database:
            id = self.database.index(element)
            words = re.findall(r'\w+', element['titulo'].lower().translate(replacements))
            for word in words:
                if word not in stopwords:
                    inverted_index[word].add(id)
        
        self.inv_index = {word: list(ids) for word, ids in inverted_index.items()}

# Asignar puerto a app segun nombre valido de base de datos
def assign_port(database):
    global slave
    slave = Slave(database)
    return slave.port

# Retornar lista de diccionario {index, ranking}
def rank_list(id_list):
    ranked_list = []
    for id in set(id_list):
        ranked_list.append({"index": id, "rank": id_list.count(id)})
    return ranked_list

# Retornar grupo etario perteneciente a la edad
def topic_interest(categories, topic, age):
    age = int(age)
    for entry in categories["categorias"]:
        if entry["nombre"] == topic:
            for age_group in categories["grupos"]:
                if age >= age_group["min"] and age <= age_group["max"]:
                    return entry[age_group["nombre"]]

# Ruta de busqueda por palabra clave
# Retorno:
#  {
#     [
#         {
#             "categoria": string,
#             "interes": int,
#             "ranking": int,
#             "tipo": string,
#             "titulo": string
#         }
#     ]
#  }
@app.route("/busqueda", methods=["GET"])
def buscar():

    start = time.time()

    # Crea variables a partir de parametros de URL
    wordlist = request.args['titulo'].split(" ")
    age = request.args['edad']
    
    # Lista de indices de documentos que contienen terminos de busqueda
    ids = []

    # Lista de resultados
    response = []

    # Llena lista de indices
    for word in wordlist:
        if word in slave.inv_index:
            for occurence in slave.inv_index[word]:
                ids.append(occurence)
    
    # Calcula ranking de elementos en lista de indices
    ranked_list = rank_list(ids)

    # Carga json que contiene subcategorias con sus respectivos interes por grupo etario
    with open('categorias.json') as category:
        categorias = json.load(category)
    
    # Agrega campos para completar estructura de retorno
    for id_rank in ranked_list:
        element = dict(slave.database[id_rank["index"]])
        element["ranking"] = id_rank["rank"]
        element["tipo"] = slave.dbname
        element["interes"] = topic_interest(categorias, element["categoria"], age)
        response.append(element)

    #preparo los datos para el log
    end = time.time()
    rango = "no dice"
    age = int(age)
    if(age > 4 and age < 17):
        rango="joven"
    elif (age > 16 and age < 44):
        rango="adulto"
    else:
        rango="mayor"

    wordlist = request.args["titulo"].replace(" ", "+")

    response_json = json.dumps(response)
    response_tamaño = sys.getsizeof(response_json)
    tamañoMB = response_tamaño / (1024 * 1024)
    #genera log
    log_line = build_log(start, end, socket.gethostname(), f"esclavo{slave.port}", wordlist, len(response), rango, tamañoMB)
    log_file = f"slave{slave.port}.log"
    log_local(log_line, log_file)
    send_logs_to_server(log_file)

    return response


# Ruta de busqueda por tipo de documento
# Retorno:
# {
#    [
#        {
#            "tipo": string,
#            "titulo": string
#        }
#    ]
# }
@app.route("/fetch_all", methods=["GET"])
def fetch_all():
    return slave.database

if __name__ == "__main__":
    # Correr app dado el nombre de una base de datos como argumento
    if (len(sys.argv) == 2):
        app.run(debug=True, port=assign_port(sys.argv[1]))
    else:
        print ("Error: base de datos no especificada\nUso: slave.py {tesis/libros/videos/documentales}")