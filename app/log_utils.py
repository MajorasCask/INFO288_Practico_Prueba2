import time
from datetime import datetime
import socket
import os

def build_log(start_time, end_time, machine, tipo, query, score, rango, tamaño):
    duration = round(end_time - start_time, 4)
    return f"{datetime.fromtimestamp(start_time)},{datetime.fromtimestamp(end_time)},{machine},{tipo},{query},{duration},{score},{rango},{tamaño}"

def log_local(log_line: str, log_file: str):
    os.makedirs("logs", exist_ok=True)
    path = os.path.join("logs", log_file)
    with open(path, "a") as f:
        f.write(log_line + "\n")
