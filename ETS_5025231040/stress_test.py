# Modul stress_test.py ini digunakan untuk melakukan stress testing pada server
# yang mendukung operasi UPLOAD dan DOWNLOAD file melalui client.
# Tujuan dari stress test ini adalah mengukur performa sistem dalam kondisi
# berbagai kombinasi ukuran file, jumlah client yang paralel (client pool),
# dan jumlah thread/proses server (server pool yang diatur manual saat menjalankan server).

import time
import concurrent.futures  # Digunakan untuk menjalankan multithreading (ThreadPoolExecutor)
import os
from client import upload_file, download_file  # Mengimpor fungsi upload dan download dari client

# Daftar ukuran file yang digunakan untuk pengujian (dalam byte)
file_sizes = {
    "10MB": 10 * 1024 * 1024,
    "50MB": 50 * 1024 * 1024,
    "100MB": 100 * 1024 * 1024
}

# Dua jenis operasi yang akan diuji: upload dan download
operations = ['UPLOAD', 'DOWNLOAD']

# Konfigurasi jumlah thread (client pool) yang digunakan untuk menjalankan klien secara paralel
# Server pool (jumlah thread server) tidak dikontrol dalam script ini, tapi diasumsikan dikontrol secara manual oleh user
client_pool_sizes = [1, 5, 50]
server_pool_sizes = [1, 5, 50]

# Folder tempat file-file sementara disimpan
TEMP_FOLDER = "temp_files"
os.makedirs(TEMP_FOLDER, exist_ok=True)  # Membuat folder jika belum ada

# Fungsi ini digunakan untuk menghasilkan file dummy biner berukuran sesuai file_sizes
# File dummy ini akan digunakan sebagai bahan untuk operasi upload
def generate_test_files():
    for label, size in file_sizes.items():
        path = os.path.join(TEMP_FOLDER, f"test_{label}.bin")
        # Hanya generate file jika belum ada, untuk menghindari regenerate yang tidak perlu
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(os.urandom(size))  # Mengisi file dengan data acak (random bytes)

# Fungsi run_worker bertugas menjalankan satu instance dari upload atau download.
# Fungsi ini akan dijalankan secara paralel oleh thread dalam thread pool.
def run_worker(op, file_path, label, idx):
    start = time.time()  # Catat waktu mulai
    if op == "UPLOAD":
        success, _ = upload_file(file_path)  # Upload file
    elif op == "DOWNLOAD":
        # Download file ke path yang spesifik untuk tiap thread (hindari overwrite)
        success, _ = download_file(os.path.basename(file_path), f"{TEMP_FOLDER}/dl_{label}_{idx}.bin")
    else:
        return None

    elapsed = time.time() - start  # Hitung waktu yang dibutuhkan untuk operasi
    size = os.path.getsize(file_path)  # Ambil ukuran file yang diproses
    throughput = size / elapsed if elapsed > 0 else 0  # Hitung kecepatan transfer dalam byte/detik

    return {
        "success": success,
        "time": elapsed,
        "throughput": throughput
    }

# Fungsi utama yang melakukan keseluruhan proses stress test
def stress_test():
    generate_test_files()  # Siapkan file dummy
    result_rows = []  # Untuk menyimpan hasil pengujian
    test_id = 1  # Penomoran pengujian

    # Loop kombinasi semua konfigurasi: operasi x ukuran file x jumlah klien x jumlah thread server
    for op in operations:
        for label, size in file_sizes.items():
            file_path = os.path.join(TEMP_FOLDER, f"test_{label}.bin")
            for client_workers in client_pool_sizes:
                for server_workers in server_pool_sizes:
                    futures = []  # List task paralel
                    successes = 0
                    failures = 0
                    total_time = 0
                    total_throughput = 0

                    # DI SINILAH MULTITHREADING DIGUNAKAN
                    # Menggunakan ThreadPoolExecutor dari modul concurrent.futures
                    # Ini berarti klien dijalankan secara paralel dengan thread (BUKAN multiprocess)
                    with concurrent.futures.ThreadPoolExecutor(max_workers=client_workers) as executor:
                        for i in range(client_workers):
                            # Kirim tugas (upload/download) ke thread pool
                            futures.append(executor.submit(run_worker, op, file_path, label, i))

                        # Tunggu semua task selesai dan kumpulkan hasilnya
                        for f in concurrent.futures.as_completed(futures):
                            res = f.result()
                            if res:
                                if res["success"]:
                                    successes += 1
                                    total_time += res["time"]
                                    total_throughput += res["throughput"]
                                else:
                                    failures += 1

                    # Simpan hasil pengujian dalam bentuk dictionary
                    row = {
                        "No": test_id,
                        "Operasi": op,
                        "Volume": label,
                        "Client Pool": client_workers,
                        "Server Pool": server_workers,
                        "Waktu Total per Client": round(total_time / successes, 2) if successes else '-',
                        "Throughput per Client": round(total_throughput / successes, 2) if successes else '-',
                        "Client Sukses/Gagal": f"{successes}/{failures}",
                        "Server Sukses/Gagal": f"{successes}/{failures}",  # Diasumsikan hasil server sama dengan klien
                    }
                    result_rows.append(row)
                    test_id += 1

    # Output hasil pengujian dalam bentuk tabel yang bisa dibaca
    print(f"{'No':<3} {'Operasi':<8} {'Volume':<6} {'Client':<6} {'Server':<6} {'Waktu':<10} {'Throughput':<12} {'Client S/G':<15} {'Server S/G':<15}")
    for row in result_rows:
        print(f"{row['No']:<3} {row['Operasi']:<8} {row['Volume']:<6} {row['Client Pool']:<6} {row['Server Pool']:<6} "
              f"{row['Waktu Total per Client']:<10} {row['Throughput per Client']:<12} {row['Client Sukses/Gagal']:<15} {row['Server Sukses/Gagal']:<15}")

# Fungsi utama akan dipanggil jika file ini dijalankan sebagai program
if __name__ == "__main__":
    stress_test()
