import socket
import logging
import os

# Konfigurasi server
server_address = ('172.16.16.101', 8889)

def make_socket(destination_address='localhost', port=12000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")

def send_command(command_str, filedata=None):
    alamat_server = server_address[0]
    port_server = server_address[1]
    sock = make_socket(alamat_server, port_server)

    logging.warning(f"sending message: {command_str}")
    if filedata:
        sock.sendall((command_str + "\r\n\r\n").encode() + filedata)
    else:
        sock.sendall((command_str + "\r\n\r\n").encode())

    data_received = b""
    while True:
        data = sock.recv(2048)
        if not data:
            break
        data_received += data
    sock.close()
    return data_received.decode(errors='ignore')

if __name__ == '__main__':
    print("Client connected to server at {}:{}\n".format(*server_address))
    print("$: ")

    while True:
        try:
            perintah = input("> ").strip()

            if perintah == "":
                continue

            if perintah.lower() == "exit":
                break

            elif perintah.startswith("list"):
                parts = perintah.split(" ", 1)
                folder = parts[1] if len(parts) == 2 else '.'
                request = f"GET /list?dir={folder} HTTP/1.0\r\nHost: localhost\r\n\r\n"
                print("here")
                response = send_command(request)
                #hasil = send_command("list")
                #print(hasil)
                # Ambil bagian body (setelah header HTTP)
                print("here")
                if "\r\n\r\n" in response:
                    _, body = response.split("\r\n\r\n", 1)
                    print(body.strip())
                else:
                    print("Respon tidak valid:")
                    print(response)

            elif perintah.lower().startswith("upload "):
                parts = perintah.split(" ", 1)
                if len(parts) != 2:
                    print("Format: upload <namafile>")
                    continue
                namafile = parts[1]
                if not os.path.exists(namafile):
                    print(f"File '{namafile}' tidak ditemukan.")
                    continue

                with open(namafile, "rb") as f:
                    filedata = f.read()

                request = f"POST /upload HTTP/1.0\r\nHost: localhost\r\nContent-Length: {len(filedata)}\r\n\r\n"
                response = send_command(request, filedata)
                print(response)

            elif perintah.lower().startswith("delete "):
                parts = perintah.split(" ", 1)
                if len(parts) != 2:
                    print("Format: delete <namafile>")
                    continue
                filename = parts[1]
                request = f"DELETE /delete?filename={filename} HTTP/1.0\r\nHost: localhost\r\n\r\n"
                response = send_command(request)
                print(response)

            else:
                print("Perintah tidak dikenali. Gunakan: list, upload <namafile>, delete <namafile>, exit")

        except KeyboardInterrupt:
            print("\nKeluar.")
            break
