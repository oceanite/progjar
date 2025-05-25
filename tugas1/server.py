from socket import *
import socket
import threading
import logging
import datetime
import sys

class ProcessTheClient(threading.Thread):
  def __init__(self, connection, address):
    self.connection = connection
    self.address = address
    threading.Thread.__init__(self)
  def run(self):
    logging.info(f"Connected from {self.address}")
    while True:
      data = self.connection.recv(32)
      if data:
        message = data.decode('utf-8')
        logging.info(f"Received from {self.address}: {message}")
        if message.startswith("QUIT") and message.endswith("\r\n"):
          logging.info(f"CLIENT {self.address} has exited")
          resp = "You exited\r\n"
          self.connection.sendall(resp.encode('utf-8'))
        elif message.startswith("TIME") and message.endswith("\r\n"):
          now = datetime.datetime.now().strftime("%H:%M:%S")
          response = f"JAM {now} \r\n"
          self.connection.sendall(response.encode('utf-8'))
        else:
          logging.info(f"CLIENT {self.address} SENT INVALID REQUEST")
          self.connection.sendall(f"Unknown command\r\n".encode())
          break
      else:
        break
    self.connection.close()

class Server(threading.Thread):
  def __init__(self):
    self.the_clients = []
    self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    threading.Thread.__init__(self)
  
  def run(self):
    self.my_socket.bind(('0.0.0.0',45000))
    self.my_socket.listen(1)
    while True:
      self.connection, self.client_address = self.my_socket.accept()
      logging.info(f"Connection from {self.client_address}")
      clt = ProcessTheClient(self.connection, self.client_address)
      clt.start()
      self.the_clients.append(clt)

def main():
  svr = Server()
  svr.start()

if __name__=="__main__":
  main()
