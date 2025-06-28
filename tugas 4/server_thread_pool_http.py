from socket import *
import socket
import time
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer

# Inisialisasi HTTP Server
httpserver = HttpServer()

# Fungsi untuk menangani 1 koneksi client
def ProcessTheClient(connection, address):
    rcv = b""
    while True:
        try:
            data = connection.recv(1024)
            if data:
                rcv += data
                if b"\r\n\r\n" in rcv:
                    #merubah input dari socket (berupa bytes) ke dalam string
					#agar bisa mendeteksi \r\n
                    decoded_data = rcv.decode(errors='ignore')
                    #end of command, proses string
					#logging.warning("data dari client: {}" . format(rcv))
                    hasil = httpserver.proses(decoded_data)
                    hasil += b"\r\n\r\n"
                    #logging.warning("balas ke  client: {}" . format(hasil))
					#hasil sudah dalam bentuk bytes
                    connection.sendall(hasil)
                    connection.close()
                    return
            else:
                break
        except OSError:
            break
    connection.close()
    return

def Server():
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    my_socket.bind(('0.0.0.0', 8885))
    my_socket.listen(5)

    print("Server is running on port 8885 (Thread Pool Mode)...")

    with ThreadPoolExecutor(max_workers=20) as executor:
        while True:
            connection, client_address = my_socket.accept()
            print(f"Incoming connection from {client_address}")
            p = executor.submit(ProcessTheClient, connection, client_address)
            the_clients.append(p)

            #menampilkan jumlah process yang sedang aktif
            aktif = [x for x in the_clients if not x.done()]
            print(f"[ACTIVE THREADS] {len(aktif)}")

# Entry point
def main():
    Server()

if __name__ == "__main__":
    main()
