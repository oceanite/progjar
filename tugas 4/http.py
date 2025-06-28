import sys
import os
import os.path
import uuid
from glob import glob
from datetime import datetime
import urllib.parse

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.txt': 'text/plain',
            '.html': 'text/html'
        }

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n".format(kode, message))
        resp.append("Date: {}\r\n".format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n".format(len(messagebody)))
        for kk in headers:
            resp.append("{}: {}\r\n".format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ''.join(resp)
        #menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
		#response harus berupa bytes
		#message body harus diubah dulu menjadi bytes
        if type(messagebody) is not bytes:
            messagebody = messagebody.encode()
        #response adalah bytes
        return response_headers.encode() + messagebody

    def proses(self, data):
        try:
            header, body = data.split("\r\n\r\n", 1)
        except ValueError:
            header = data
            body = ""

        lines = header.split("\r\n")
        baris = lines[0]
        all_headers = [n for n in lines[1:] if n != '']
        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            if method == 'GET':
                object_address = j[1].strip()
                return self.http_get(object_address, all_headers)
            elif method == 'POST':
                object_address = j[1].strip()
                return self.http_post(object_address, all_headers, body)
            elif method == 'DELETE':
                object_address = j[1].strip()
                return self.http_delete(object_address, all_headers)
            else:
                return self.response(400, 'Bad Request', '', {})
        except IndexError:
            return self.response(400, 'Bad Request', '', {})

    def http_get(self, object_address, headers):
        if object_address == '/':
            return self.response(200, 'OK', 'Ini Adalah Web Server Percobaan', {'Content-type': 'text/plain'})


        if object_address.startswith('/list'):
            print("List request received")
            parsed = urllib.parse.urlparse(object_address)
            query = urllib.parse.parse_qs(parsed.query)
            path = query.get('dir', ['.'])[0]

            if not os.path.exists(path):
                return self.response(404, 'Not Found', 'Directory not found', {})

            if not os.path.isdir(path):
                return self.response(400, 'Bad Request', 'Target is not a directory', {})

            try:
                entries = os.listdir(path)
                entries = sorted(entries)

                filtered = []
                for entry in entries:
                    if entry.startswith('.'):
                        continue
                    full_path = os.path.join(path, entry)
                    if os.path.isdir(full_path):
                        filtered.append(entry + "/")  # folder
                    else:
                        filtered.append(entry)        # file

                body = '\n'.join(filtered) if filtered else "No files found"
                return self.response(200, 'OK', body, {'Content-type': 'text/plain'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e), {})


        thedir = './'
        filepath = os.path.join(thedir, object_address.lstrip('/'))

        if not os.path.isfile(filepath):
            return self.response(404, 'Not Found', 'File not found', {})

        with open(filepath, 'rb') as fp:
            isi = fp.read()

        fext = os.path.splitext(filepath)[1]
        content_type = self.types.get(fext, 'application/octet-stream')
        headers = {'Content-type': content_type}

        return self.response(200, 'OK', isi, headers)

    def http_post(self, object_address, headers, body):
        if object_address == '/upload':
            filename = f"upload-{uuid.uuid4().hex[:8]}.bin"
            folder = './uploads'
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(body.encode())  # body dianggap sebagai string (raw binary client harus diubah kalau mau full biner)
                return self.response(200, 'OK', f'{filename} uploaded', {'Content-type': 'text/plain'})
            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e), {})
        else:
            return self.response(404, 'Not Found', 'POST target unknown', {})

    def http_delete(self, object_address, headers):
        parsed = urllib.parse.urlparse(object_address)
        query = urllib.parse.parse_qs(parsed.query)
        filename = query.get('filename', [None])[0]

        if not filename:
            return self.response(400, 'Bad Request', 'filename query param is required', {})

        #filepath = os.path.join('./uploads', filename)
        filepath = os.path.normpath(os.path.join('.', filename))


        if not os.path.exists(filepath):
            return self.response(404, 'Not Found', 'file not found', {})

        try:
            os.remove(filepath)
            return self.response(200, 'OK', f'{filename} deleted', {'Content-type': 'text/plain'})
        except Exception as e:
            return self.response(500, 'Internal Server Error', str(e), {})

# Test manual
#if __name__ == "__main__":
#    httpserver = HttpServer()
#    d = httpserver.proses('GET /list HTTP/1.0\r\n\r\n')
#    print(d.decode())
