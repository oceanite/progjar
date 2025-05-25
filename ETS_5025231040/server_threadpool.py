# Mengimpor modul-modul yang dibutuhkan
import socket               # Untuk komunikasi jaringan
import os                   # Untuk operasi sistem dan file
from concurrent.futures import ThreadPoolExecutor  # Untuk membuat thread pool
import logging              # Untuk mencatat log (aktivitas atau error)

# Mengatur level logging menjadi WARNING
logging.basicConfig(level=logging.WARNING)

# Alamat dan port server yang digunakan untuk menerima koneksi
SERVER_ADDRESS = ('0.0.0.0', 50900)  # 0.0.0.0 artinya menerima koneksi dari semua IP
MAX_WORKERS = 50  # Jumlah maksimum thread yang aktif dalam pool

# Fungsi untuk menangani setiap koneksi klien
def handle_client(conn, addr):
    logging.warning(f"Connected by {addr}")  # Menampilkan alamat klien yang terhubung

    try:
        # Menerima data dari klien (max 1024 byte), decode dari byte ke string
        data = conn.recv(1024).decode().strip()

        if not data:  # Jika tidak ada data diterima, keluar dari fungsi
            return

        logging.warning(f"Command: {data}")  # Menampilkan perintah dari klien

        # Memisahkan perintah berdasarkan spasi
        command_parts = data.split()
        command = command_parts[0]  # Bagian pertama adalah jenis perintah

        # === UPLOAD ===
        if command == 'UPLOAD':
            filename = command_parts[1]        # Nama file
            filesize = int(command_parts[2])   # Ukuran file dalam byte

            # Membuka file untuk ditulis dalam mode biner
            with open(filename, 'wb') as f:
                remaining = filesize  # Sisa byte yang perlu diterima
                while remaining > 0:
                    # Menerima chunk data maksimal 4096 byte
                    chunk = conn.recv(min(4096, remaining))
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)  # Mengurangi sisa byte

            conn.send(b'OK')  # Mengirim balasan ke klien bahwa upload berhasil

        # === DOWNLOAD ===
        elif command == 'DOWNLOAD':
            filename = command_parts[1]

            # Mengecek apakah file ada di direktori
            if not os.path.exists(filename):
                conn.send(b'NOTFOUND')  # File tidak ditemukan
                return

            filesize = os.path.getsize(filename)  # Mengambil ukuran file
            conn.send(f"{filesize}".encode())     # Mengirim ukuran ke klien

            # Membuka file dan mengirim isinya dalam bentuk chunk
            with open(filename, 'rb') as f:
                while chunk := f.read(4096):  # Membaca maksimal 4096 byte
                    conn.sendall(chunk)

        # === LIST ===
        elif command == 'LIST':
            files = os.listdir('.')              # Mengambil daftar file di direktori saat ini
            response = '\n'.join(files)          # Menggabungkan nama file jadi satu string
            conn.send(response.encode())         # Mengirim ke klien

        # === INVALID COMMAND ===
        else:
            conn.send(b'INVALID')  # Perintah tidak dikenali

    except Exception as e:
        logging.warning(f"Error: {e}")  # Menangkap dan mencetak error jika ada
    finally:
        conn.close()  # Menutup koneksi setelah selesai

# Fungsi utama untuk menjalankan server
def main():
    # Membuat socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(SERVER_ADDRESS)  # Mengikat socket ke alamat dan port
        s.listen()              # Mulai mendengarkan koneksi dari klien

        logging.warning(f"Server listening on {SERVER_ADDRESS}")

        # Membuat ThreadPoolExecutor dengan jumlah thread sesuai MAX_WORKERS
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while True:
                conn, addr = s.accept()  # Menerima koneksi dari klien
                # Menyerahkan tugas menangani koneksi ke thread pool
                executor.submit(handle_client, conn, addr)

# Menjalankan fungsi main jika file ini dijalankan langsung
if __name__ == "__main__":
    main()
