import socket
import sys
import _thread
import time
import os
from datetime import datetime
import json

# Configure server
HOST = "127.0.0.1"
PORT = 80
MAX_CONNECTION = 100
BUFFER_SIZE = 8192
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"

# Configure chunk
CHUNK_SIZE = 8192
CRLF = "\r\n"
LAST_CHUNK = "0000".encode('utf-8') + CRLF.encode('utf-8')
TIME_DELAY = 0  


# Convert data to chunks
def data_to_chunks(data, chunk_size):
    data_size = len(data)
    data_chunks = []
    for i in range(0, data_size - 1):
        if (i % chunk_size) == 0:
            chunk = data[i:(i + chunk_size)]
            data_chunks.append(chunk)
        elif i == data_size:
            chunk = data[data_size - (i % chunk_size):data_size - 1]
            data_chunks.append(chunk)
    return data_chunks


def format_chunk(chunk):
    return ("%X" % len(chunk)).encode('utf-8') + CRLF.encode('utf-8') + chunk + CRLF.encode('utf-8')


def data_to_map_chunks(res, chunk_size):
    return map(format_chunk, data_to_chunks(res, chunk_size))


# Read a file
def read_file(file_name):
    try:
        file = open(file_name, 'rb')
        data = file.read()
        file.close()
    except IOError:
        print("Read file error!")
        data = "".encode('utf-8')
    return data


# Handle response to client (case normal)
def response_to_client(header, response, connection):
    final_response = header.encode('utf-8')
    final_response += response
    print("[=] Server response header:")
    print(header)
    print()
    connection.send(final_response)
    connection.close()


# Handle files to download
def file_time(file_name):
    return str(datetime.fromtimestamp(os.path.getmtime(file_name))).split('.')[0]


def folder_size(folder_name):
    if os.path.isfile(folder_name):
        return os.path.getsize(folder_name)
    else:
        total_size = 0
        for x in os.listdir(os.chdir(folder_name)):
            root = os.getcwd()
            total_size += folder_size(x)
            if not (os.path.isfile(x)):
                os.chdir(root)
        return total_size


def file_size(file_name):
    root = os.getcwd()
    size = folder_size(file_name)
    os.chdir(root)
    currency = [" B", " KB", " MB", " GB"]
    i = 0
    while size > 1024:
        i += 1
        size = round(size / 1024, 2)
    return str(size) + currency[i]


def load_files(folder_request):
    js1 = {}
    array = {}
    root = os.getcwd()
    os.chdir(folder_request)
    for x in os.listdir(os.getcwd()):
        if folder_request != '.':
            js1['path'] = '/' + folder_request + '/' + x
        else:
            js1['path'] = '/' + x
        js1['size'] = file_size(x)
        js1['time'] = file_time(x)
        array[x] = js1
        js1 = {}
    os.chdir(root)
    json_file = open('html/files.json', 'w')
    json.dump(array, json_file, indent=len(array))
    json_file.close()


# Handle request from client
def handle_request(connection, address, request):
    line_list = request.split(CRLF)
    request_line = line_list[0]
    method = request_line.split(' ')[0]
    file_request = request_line.split(' ')[1].lstrip('/').split('?')[0]
    http_ver = request_line.split(' ')[2]
    file_request = file_request.replace("%20", " ")

    print("[>] Client is: ", address)
    print("[>] Client requested file: ", file_request)
    print()
    if file_request == "":  # Make index.html as homepage
        header = http_ver + " 301 Moved Permanently" + CRLF
        header += "Location: http://127.0.0.1:80/index.html" + CRLF
        header += "Server: Localhost" + CRLF
        response = "".encode('utf-8')
        response_to_client(header, response, connection)
    else:
        try:
            if method == "POST":  # Request to login
                info = line_list[-1].split("&")
                username = info[0].split('=')[1]
                password = info[1].split('=')[1]
                # The correct information is logged in
                if (username == DEFAULT_USERNAME) and (password == DEFAULT_PASSWORD):
                    print("[V] Login successfully !")
                    header = http_ver + " 303 See Other" + CRLF
                    header += "Location: http://127.0.0.1:80/info.html" + CRLF
                    header += "Server: Localhost" + CRLF
                    response = "".encode('utf-8')
                    response_to_client(header, response, connection)
                else:  # Incorrect information
                    print("[!] Incorrect username or password !")
                    response = read_file("html/404.html")
                    header = http_ver + " 404 Not Found" + CRLF
                    header += "Server: Localhost" + CRLF
                    header += "Content-Type: text/html" + CRLF
                    header += "Content-Length: " + str(len(response)) + " bytes" + CRLF + CRLF
                    response_to_client(header, response, connection)
            elif (file_request == "index.html") or (file_request == "info.html"):  # Request html default
                response = read_file("html/" + file_request)
                header = http_ver + " 200 OK" + CRLF
                header += "Server: Localhost" + CRLF
                header += "Content-Type: text/html" + CRLF
                header += "Content-Length: " + str(len(response)) + " bytes" + CRLF + CRLF
                response_to_client(header, response, connection)
            else:  # Request files.html and other files in this page
                mime_dict = {".html": "text/html",
                             ".jpeg": "image/jpeg",
                             ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document}",
                             ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                             ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             ".pdf": "application/pdf",
                             ".mp3": "audio/mpeg",
                             ".mpg": "video/mpeg",
                             ".png": "image/png",
                             ".jpg": "image/jpeg",
                             ".css": "text/css",
                             ".mp4": "video/mp4",
                             ".m4a": "audio/m4a",
                             ".rar": "application/rar",
                             ".txt": "text/plain",
                             ".js": "text/javascript",
                             ".json": "application/json",
                             ".ico": "image/x-icon",
                             ".zip": "application/zip",
                             "": "text/html"}
                root_ext = os.path.splitext(file_request)
                header = http_ver + " 200 OK" + CRLF
                header += "Server: Localhost" + CRLF
                header += "Content-Type: " + mime_dict[root_ext[1].lower()] + CRLF
                header += "Transfer-Encoding: chunked" + CRLF + CRLF
                connection.send(header.encode('utf-8'))
                print("[=] Server response header:")
                print(header)
                print()
                if root_ext[1] == ".html": # Access to files.html
                    load_files("files")
                    response = read_file("html/" + file_request.split('/')[-1])
                elif root_ext[1] == ".json" or root_ext[1] == ".js":
                    response = read_file("html/" + file_request.split('/')[-1])
                elif root_ext[1] == "": # Access to folder
                    root = os.getcwd()
                    load_files(root_ext[0])
                    os.chdir(root)
                    response = read_file("html/files.html")
                elif root_ext[0] == "avatar1" or root_ext[0] == "avatar2" or root_ext[0] == "favicon": # Access to elements of html
                    response = read_file("img/" + file_request.split('/')[-1])
                else: # Access to normal file
                    response = read_file(file_request)
                chunks = data_to_map_chunks(response, CHUNK_SIZE) # Split file into chunks
                for chunk in chunks:
                    connection.send(chunk)
                    time.sleep(TIME_DELAY)  # Time delay between chunks
                connection.send(LAST_CHUNK)
                connection.send(CRLF.encode('utf-8'))
                connection.close()
        except Exception as e:
            print(e)
            response = read_file("html/404.html")
            header = http_ver + " 404 Not Found" + CRLF
            header += "Server: Localhost" + CRLF
            header += "Content-Type: text/html" + CRLF
            header += "Content-Length: " + str(len(response)) + " bytes" + CRLF + CRLF
            response_to_client(header, response, connection)


# Build class server
class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(MAX_CONNECTION)

        print("[>] Server running on %s:%s" % (HOST, PORT))

    def run(self):
        while True:
            try:
                (connection, address) = self.server.accept()
                request = connection.recv(BUFFER_SIZE).decode('utf-8')
                _thread.start_new_thread(handle_request, (connection, address, request))
            except KeyboardInterrupt:
                self.server.close()

                print("[!] Finished connection !")
                sys.exit(1)


if __name__ == "__main__":
    Server().run()
