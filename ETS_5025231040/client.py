import socket
import os
import logging

logging.basicConfig(level=logging.WARNING)

SERVER_ADDRESS = ('172.16.16.101', 50900)


def upload_file(filename):
    if not os.path.exists(filename):
        return False, "File not found"

    filesize = os.path.getsize(filename)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(SERVER_ADDRESS)
            s.sendall(f"UPLOAD {os.path.basename(filename)} {filesize}".encode())
            with open(filename, 'rb') as f:
                while chunk := f.read(4096):
                    s.sendall(chunk)
            response = s.recv(1024)
            return response == b'OK', response.decode()
    except Exception as e:
        return False, str(e)


def download_file(filename, save_as=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(SERVER_ADDRESS)
            s.sendall(f"DOWNLOAD {filename}".encode())
            response = s.recv(1024)
            if response == b'NOTFOUND':
                return False, "File not found"
            filesize = int(response.decode())
            save_as = save_as or filename
            with open(save_as, 'wb') as f:
                remaining = filesize
                while remaining > 0:
                    chunk = s.recv(min(4096, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            return True, "Download complete"
    except Exception as e:
        return False, str(e)


def list_files():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(SERVER_ADDRESS)
            s.sendall(b"LIST")
            response = s.recv(8192)
            return True, response.decode()
    except Exception as e:
        return False, str(e)
