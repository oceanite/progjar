import time
import concurrent.futures
import socket
import os
import uuid
import random

# Konfigurasi server
SERVER_HOST = "172.16.16.101"
SERVER_PORT = 8885

# Jumlah client paralel untuk diuji
CLIENT_POOL_SIZES = [1, 5, 10, 20]

# Ukuran file untuk upload
UPLOAD_FILE_SIZES = {
    "1KB": 1024,
    "100KB": 100 * 1024,
    "1MB": 1024 * 1024,
}

# Daftar operasi yang akan diuji
OPERATIONS = ['list', 'upload', 'delete']


def generate_dummy_data(size):
    return os.urandom(size)


def send_request(request_bytes, body_bytes=b""):
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall(request_bytes)
        if body_bytes:
            s.sendall(body_bytes)

        response = b""
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            response += chunk

        s.close()
        return True, response
    except:
        return False, b""


def run_worker(op, label=None, size=0, idx=0):
    try:
        if op == "list":
            request = b"GET /list?dir=. HTTP/1.0\r\nHost: localhost\r\n\r\n"
            start = time.time()
            ok, _ = send_request(request)
            return ok, time.time() - start

        elif op == "upload":
            data = generate_dummy_data(size)

            request_header = (
                f"POST /upload HTTP/1.0\r\n"
                f"Host: localhost\r\n"
                f"Content-Length: {len(data)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode()

            try:
                s = socket.socket()
                s.settimeout(10)
                s.connect((SERVER_HOST, SERVER_PORT))

                start = time.time()
                s.sendall(request_header)
                s.sendall(data)  # kirim data setelah header

                response = b""
                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    response += chunk

                elapsed = time.time() - start
                s.close()
                return True, elapsed
            except Exception as e:
                print(f"[UPLOAD ERROR] {e}")
                return False, 0


        elif op == "delete":
            fake_file = f"uploads/fake-{uuid.uuid4().hex[:6]}.txt"
            request = (
                f"DELETE /delete?filename={fake_file} HTTP/1.0\r\n"
                f"Host: localhost\r\n\r\n"
            ).encode()
            start = time.time()
            ok, _ = send_request(request)
            return ok, time.time() - start

    except:
        return False, 0


def stress_test():
    test_id = 1
    print(f"{'No':<3} {'Operasi':<8} {'Ukuran':<8} {'Clients':<7} {'Sukses':<8} {'Gagal':<8} {'Rata2 Waktu (s)':<16}")

    for op in OPERATIONS:
        sizes = UPLOAD_FILE_SIZES.items() if op == "upload" else [("N/A", 0)]
        for label, size in sizes:
            for clients in CLIENT_POOL_SIZES:
                futures = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=clients) as executor:
                    for i in range(clients):
                        futures.append(executor.submit(run_worker, op, label, size, i))

                    sukses = 0
                    gagal = 0
                    total_time = 0

                    for f in concurrent.futures.as_completed(futures):
                        ok, t = f.result()
                        if ok:
                            sukses += 1
                            total_time += t
                        else:
                            gagal += 1

                avg_time = round(total_time / sukses, 4) if sukses else "-"
                print(f"{test_id:<3} {op:<8} {label:<8} {clients:<7} {sukses:<8} {gagal:<8} {avg_time:<16}")
                test_id += 1


if __name__ == "__main__":
    print("Memulai stress test...")
    print(f"Server: {SERVER_HOST}:{SERVER_PORT}") 
    stress_test()
