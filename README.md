# INFO288 - Práctico Prueba 2

## Especificaciones
- Lenguaje: Python 3.10.1
- Framework: Flask

## Preparación
- Instalar Flask y Pyro5
   ```bash
   pip install Flask
   pip install Pyro5

## Despliegue
1. Ejecutar esclavos en distintas terminales, cada uno con una base de datos distinta como argumento.
    ```bash
    slave.py {tesis|libros|videos|documentales}
2. Ejecutar maestro, también en su propia terminal.
    ```bash
    master.py

3. Ejecutar El servidor RMI, también en su propia terminal.
    ```bash
    log_server.py

4. Si se solicita, permitir acceso de Firewall

