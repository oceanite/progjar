from socket import *
import socket
import os
import logging
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer


def handle_request(data_str):
    from http import HttpServer  # import lokal
    server = HttpServer()    # buat instance baru di dalam process
    print(f"Processing request in process PID {os.getpid()}")
    hasil = server.proses(data_str)
    return hasil + b"\r\n\r\n"

def Server():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.bind(('0.0.0.0', 8889))
    my_socket.listen(20)
    print("Process Pool HTTP Server running on port 8889")

    with ProcessPoolExecutor(5) as executor:
        while True:
            connection, client_address = my_socket.accept()
            print(f"Accepted connection from {client_address}")
            connection.settimeout(10)
            try:
                data = b""
                while True:
                    chunk = connection.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if b"\r\n\r\n" in data:
                        break

                if not data:
                    connection.close()
                    continue

                request_str = data.decode(errors='ignore')
                future = executor.submit(handle_request, request_str)
                hasil = future.result(timeout=10)

                connection.sendall(hasil)

            except Exception as e:
                logging.warning(f"Error: {e}")
            finally:
                connection.close()

import multiprocessing

def main():
    multiprocessing.set_start_method("spawn", force=True) 
    Server()

if __name__ == "__main__":
    main()
