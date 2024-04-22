from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import subprocess

# Función para obtener los IDs PCI de las tarjetas GPU disponibles en el servidor
def obtener_pci_ids_disponibles(servidor):
    try:
        comando = f"pvesh get /nodes/{servidor}/hardware/pci | grep NVIDIA | grep -Ev Audio"
        salida = subprocess.check_output(comando, shell=True)
        lineas = salida.decode().strip().split('\n')
        pci_ids = [line.split()[2] for line in lineas]
        return pci_ids
    except subprocess.CalledProcessError as e:
        print("Error al ejecutar pvesh:", e.output.decode())
        return []

# Función para obtener las tarjetas GPU disponibles en el servidor
def obtener_tarjetas_gpu_disponibles(servidor):
    pci_ids = obtener_pci_ids_disponibles(servidor)
    return pci_ids

# Función para obtener las tarjetas GPU actualmente en uso
def obtener_tarjetas_gpu_en_uso():
    try:
        comando = "cat /etc/pve/qemu-server/*.conf | grep pcie | awk '{print $1}' FS='[/,]' | awk '{print $2}'"
        salida = subprocess.check_output(comando, shell=True)
        tarjetas_en_uso = salida.decode().strip().split('\n')
        return tarjetas_en_uso
    except subprocess.CalledProcessError as e:
        print("Error al ejecutar el comando:", e.output.decode())
        return []

# Función para verificar si una tarjeta GPU está libre
def gpu_libre(tarjetas_disponibles, tarjetas_en_uso):
    for tarjeta in tarjetas_disponibles:
        if tarjeta not in tarjetas_en_uso:
            return tarjeta
    return None

# Clase para manejar las peticiones HTTP
class GPURequestHandler(BaseHTTPRequestHandler):
    # Manejar las peticiones GET
    def do_GET(self):
        if self.path.startswith('/gpu/'):
            # Obtener el nombre del servidor de la URL
            servidor = self.path.split('/')[2]

            if not servidor:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Falta el nombre del servidor en la URL"}).encode())
                return

            if self.path.startswith('/gpu/libre/'):
                # Obtener las tarjetas GPU disponibles en el servidor
                tarjetas_disponibles = obtener_tarjetas_gpu_disponibles(servidor)
                tarjetas_en_uso = obtener_tarjetas_gpu_en_uso()
                tarjeta_libre = gpu_libre(tarjetas_disponibles, tarjetas_en_uso)
                print("Tarjetas disponibles:", tarjetas_disponibles)
                print("Tarjetas en uso:", tarjetas_en_uso)
                print("Tarjeta libre:", tarjeta_libre)
                if tarjeta_libre:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"tarjeta_libre": tarjeta_libre}).encode())
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"mensaje": "No hay tarjetas GPU libres"}).encode())
            else:
                # Obtener las tarjetas GPU disponibles en el servidor
                tarjetas_disponibles = obtener_tarjetas_gpu_disponibles(servidor)
                tarjetas_en_uso = obtener_tarjetas_gpu_en_uso()
                print("Tarjetas disponibles:", tarjetas_disponibles)
                print("Tarjetas en uso:", tarjetas_en_uso)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "servidor": servidor,
                    "tarjetas_disponibles": tarjetas_disponibles,
                    "tarjetas_en_uso": tarjetas_en_uso
                }).encode())
        else:
            self.send_error(404)

# Función para ejecutar el servidor
def run(server_class=HTTPServer, handler_class=GPURequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

# Iniciar el servidor
if __name__ == '__main__':
    run()
