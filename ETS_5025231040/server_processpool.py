import socket
import os
import logging
import multiprocessing

logging.basicConfig(level=logging.WARNING)

SERVER_ADDRESS = ('0.0.0.0', 50900)
MAX_WORKERS = 50  # Jumlah maksimal worker

# Gunakan Semaphore untuk membatasi jumlah worker yang aktif
semaphore = multiprocessing.BoundedSemaphore(MAX_WORKERS)

def handle_client(conn, addr):
    with semaphore:
        logging.warning(f"Connected by {addr}")
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                return
            logging.warning(f"Command: {data}")
            command_parts = data.split()
            command = command_parts[0]

            if command == 'UPLOAD':
                filename = command_parts[1]
                filesize = int(command_parts[2])
                with open(filename, 'wb') as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = conn.recv(min(4096, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                conn.send(b'OK')

            elif command == 'DOWNLOAD':
                filename = command_parts[1]
                if not os.path.exists(filename):
                    conn.send(b'NOTFOUND')
                    return
                filesize = os.path.getsize(filename)
                conn.send(f"{filesize}".encode())
                with open(filename, 'rb') as f:
                    while chunk := f.read(4096):
                        conn.sendall(chunk)

            elif command == 'LIST':
                files = os.listdir('.')
                response = '\n'.join(files)
                conn.send(response.encode())

            else:
                conn.send(b'INVALID')

        except Exception as e:
            logging.warning(f"Error: {e}")
        finally:
            conn.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(SERVER_ADDRESS)
        s.listen()
        logging.warning(f"Server listening on {SERVER_ADDRESS}")
        while True:
            conn, addr = s.accept()
            p = multiprocessing.Process(target=handle_client, args=(conn, addr))
            p.daemon = True
            p.start()
            conn.close()

#if __name__ == "__main__":
#    multiprocessing.set_start_method('fork')  # or 'spawn' on Windows
#    main()
if __name__ == '__main__':
    # Tambahkan proteksi agar hanya dipanggil sekali
    try:
        multiprocessing.set_start_method('fork')
    except RuntimeError:
        pass  # Sudah diset, abaikan
    main()
