import time
import concurrent.futures
import os
from client import upload_file, download_file

# Konfigurasi stress test
file_sizes = {
    "10MB": 10 * 1024 * 1024,
    "50MB": 50 * 1024 * 1024,
    "100MB": 100 * 1024 * 1024
}
operations = ['UPLOAD', 'DOWNLOAD']
client_pool_sizes = [1, 5, 50]
server_pool_sizes = [1, 5, 50]  # catatan: ini kamu atur manual saat run servernya

TEMP_FOLDER = "temp_files"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Generate dummy files
def generate_test_files():
    for label, size in file_sizes.items():
        path = os.path.join(TEMP_FOLDER, f"test_{label}.bin")
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(os.urandom(size))

def run_worker(op, file_path, label, idx):
    start = time.time()
    if op == "UPLOAD":
        success, _ = upload_file(file_path)
    elif op == "DOWNLOAD":
        success, _ = download_file(os.path.basename(file_path), f"{TEMP_FOLDER}/dl_{label}_{idx}.bin")
    else:
        return None

    elapsed = time.time() - start
    size = os.path.getsize(file_path)
    throughput = size / elapsed if elapsed > 0 else 0
    return {
        "success": success,
        "time": elapsed,
        "throughput": throughput
    }

def stress_test():
    generate_test_files()
    result_rows = []
    test_id = 1

    for op in operations:
        for label, size in file_sizes.items():
            file_path = os.path.join(TEMP_FOLDER, f"test_{label}.bin")
            for client_workers in client_pool_sizes:
                for server_workers in server_pool_sizes:
                    futures = []
                    successes = 0
                    failures = 0
                    total_time = 0
                    total_throughput = 0

                    with concurrent.futures.ThreadPoolExecutor(max_workers=client_workers) as executor:
                        for i in range(client_workers):
                            futures.append(executor.submit(run_worker, op, file_path, label, i))

                        for f in concurrent.futures.as_completed(futures):
                            res = f.result()
                            if res:
                                if res["success"]:
                                    successes += 1
                                    total_time += res["time"]
                                    total_throughput += res["throughput"]
                                else:
                                    failures += 1

                    row = {
                        "No": test_id,
                        "Operasi": op,
                        "Volume": label,
                        "Client Pool": client_workers,
                        "Server Pool": server_workers,
                        "Waktu Total per Client": round(total_time / successes, 2) if successes else '-',
                        "Throughput per Client": round(total_throughput / successes, 2) if successes else '-',
                        "Client Sukses/Gagal": f"{successes}/{failures}",
                        "Server Sukses/Gagal": f"{successes}/{failures}",  # diasumsikan sama
                    }
                    result_rows.append(row)
                    test_id += 1

    # Output tabel
    print(f"{'No':<3} {'Operasi':<8} {'Volume':<6} {'Client':<6} {'Server':<6} {'Waktu':<10} {'Throughput':<12} {'Client S/G':<15} {'Server S/G':<15}")
    for row in result_rows:
        print(f"{row['No']:<3} {row['Operasi']:<8} {row['Volume']:<6} {row['Client Pool']:<6} {row['Server Pool']:<6} "
              f"{row['Waktu Total per Client']:<10} {row['Throughput per Client']:<12} {row['Client Sukses/Gagal']:<15} {row['Server Sukses/Gagal']:<15}")

if __name__ == "__main__":
    stress_test()
