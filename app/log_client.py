import os
import Pyro5.api

def send_logs_to_server(log_file: str):
    uri = "PYRO:logserver@localhost:9090"
    try:
        server = Pyro5.api.Proxy(uri)
        path = os.path.join("logs", log_file)
        if not os.path.exists(path):
            print(f"No se encontró el archivo {log_file}")
            return

        with open(path, "r") as f:
            for line in f:
                server.receive_log(line.strip())
        print(f"Logs de {log_file} enviados al servidor.")
    except Exception as e:
        print("Error al conectar al servidor RMI:", e)
