# Import modul-modul yang diperlukan
import socket                      # Untuk komunikasi jaringan
import os                          # Untuk operasi file dan path
import logging                     # Untuk mencatat aktivitas dan error
import multiprocessing             # Untuk membuat proses-proses paralel

# Mengatur level logging ke WARNING agar hanya mencatat peringatan dan error
logging.basicConfig(level=logging.WARNING)

# Alamat dan port yang digunakan server untuk menerima koneksi
SERVER_ADDRESS = ('0.0.0.0', 50900)  # 0.0.0.0 berarti menerima dari semua alamat IP
MAX_WORKERS = 50  # Jumlah maksimal proses aktif sekaligus

# Menggunakan semaphore untuk membatasi jumlah proses aktif agar tidak melebihi MAX_WORKERS
semaphore = multiprocessing.BoundedSemaphore(MAX_WORKERS)

# Fungsi untuk menangani satu klien (dijalankan dalam proses terpisah)
def handle_client(conn, addr):
    with semaphore:  # Membatasi jumlah proses aktif menggunakan semaphore
        logging.warning(f"Connected by {addr}")  # Log alamat klien yang terhubung
        try:
            # Menerima data awal dari klien (perintah), decode dari byte ke string
            data = conn.recv(1024).decode().strip()
            if not data:
                return

            logging.warning(f"Command: {data}")  # Tampilkan perintah yang diterima
            command_parts = data.split()        # Pisahkan perintah dari parameter
            command = command_parts[0]          # Ambil jenis perintah

            # === Perintah UPLOAD ===
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
                conn.send(b'OK')  # Kirim balasan bahwa upload sukses

            # === Perintah DOWNLOAD ===
            elif command == 'DOWNLOAD':
                filename = command_parts[1]
                if not os.path.exists(filename):
                    conn.send(b'NOTFOUND')  # Kirim jika file tidak ada
                    return
                filesize = os.path.getsize(filename)
                conn.send(f"{filesize}".encode())  # Kirim ukuran file terlebih dahulu
                with open(filename, 'rb') as f:
                    while chunk := f.read(4096):
                        conn.sendall(chunk)

            # === Perintah LIST ===
            elif command == 'LIST':
                files = os.listdir('.')           # Ambil daftar file di direktori saat ini
                response = '\n'.join(files)       # Gabungkan jadi satu string
                conn.send(response.encode())      # Kirim daftar file ke klien

            # === Perintah Tidak Dikenali ===
            else:
                conn.send(b'INVALID')  # Kirim pesan invalid jika perintah tak dikenali

        except Exception as e:
            logging.warning(f"Error: {e}")  # Tampilkan pesan error jika terjadi
        finally:
            conn.close()  # Tutup koneksi setelah selesai

# Fungsi utama server
def main():
    # Membuat socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Agar port bisa digunakan ulang
        s.bind(SERVER_ADDRESS)  # Mengikat socket ke alamat dan port
        s.listen()              # Mulai mendengarkan koneksi masuk
        logging.warning(f"Server listening on {SERVER_ADDRESS}")

        while True:
            conn, addr = s.accept()  # Menerima koneksi klien
            # Buat proses baru untuk menangani klien tersebut
            p = multiprocessing.Process(target=handle_client, args=(conn, addr))
            p.daemon = True  # Supaya proses tidak menghalangi terminasi utama
            p.start()
            conn.close()  # Tutup koneksi di proses utama, biarkan proses baru yang pakai

# Proteksi agar hanya dijalankan jika file utama, dan set metode start multiprocessing
if __name__ == '__main__':
    try:
        # Set metode start multiprocessing ke 'fork'. Jika sudah diset, abaikan error.
        multiprocessing.set_start_method('fork')
    except RuntimeError:
        pass
    main()
