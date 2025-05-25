from socket import *
import socket
import threading
import time
import sys
import logging



try:
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = ('172.16.16.101', 32444)
    logging.info(f"connecting to {server_address}")
    sock.connect(server_address)

    while True:
        request = input("YOU: ")
        if request == "QUIT":
            sock.sendall(request.encode())
            print("Exiting...")
            sock.close()
            print("Exited successfully.")
            exit()
        elif request.startswith("TIME"):
            request += "\r\n"
            sock.sendall(request.encode())
            message = sock.recv(14)
            if len(message) == 14:
                print(message.decode('utf-8'))
            else:
                print("Invalid response!")  
except Exception as ee:
    logging.info(f"ERROR: {str(ee)}")
    exit(0)

finally:
    logging.info("Closing..")
    sock.close()
