from socket import *
import socket
import threading
import time
import sys
import logging

def recv_until(sock, delimiter=b"\r\n"):
    data = b""
    while not data.endswith(delimiter):
        part = sock.recv(1)
        if not part:
            break
        data += part
    return data

try:
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('172.16.16.101', 45000)
    logging.info(f"connecting to {server_address}")
    sock.connect(server_address)

    while True:
        request = input("[YOU]: ")
        request += "\r\n"
        sock.sendall(request.encode())
        message = recv_until(sock)
        if request[:4] == "QUIT":
            print("Exiting...")
            print("[SERVER]: "+ message.decode('utf-8'))        
            sock.close()
            print("Exited successfully.")
            exit()
        else:
            print("[SERVER]: "+ message.decode('utf-8'))            

except Exception as ee:
    logging.info(f"ERROR: {str(ee)}")
    exit(0)

finally:
    logging.info("Closing..")
    sock.close()
