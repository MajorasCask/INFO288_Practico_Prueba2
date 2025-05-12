import os
from datetime import datetime
from log_interface import LogInterface
import Pyro5.api

@Pyro5.api.expose
class LogServer(LogInterface):
    def __init__(self):
        self.log_file = "centralized_log.log"
        # Crear el archivo si no existe
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("# timestamp_ini,timestamp_fin,máquina,tipo_máquina,query,tiempo_total,score,rango_etario,Tamaño_en_MB\n")

    def receive_log(self, log_line: str):
        log_line = log_line.strip()
        # Leer todas las líneas existentes
        existing_lines = set()
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                existing_lines = set(line.strip() for line in f if not line.startswith("#"))

        # Evitar duplicados
        if log_line not in existing_lines:
            with open(self.log_file, "a") as f:
                f.write(log_line + "\n")
            print(f"[{datetime.now()}] Log nuevo recibido y guardado.")
        else:
            print(f"[{datetime.now()}] Log duplicado ignorado.")

# Inicializa el servidor Pyro5
daemon = Pyro5.server.Daemon(host="localhost", port=9090)
uri = daemon.register(LogServer(), "logserver")
print("Servidor RMI activo en:", uri)
daemon.requestLoop()
