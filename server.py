import socket
import threading
import os
import datetime

SERVER_HOST = '0.0.0.0'  # Listen on all available network interfaces
SERVER_PORT = 12345
BUFFER_SIZE = 1024
DIRECTORY = "server_files"

# Ensure the directory exists
os.makedirs(DIRECTORY, exist_ok=True)

clients = {}

def handle_client(client_socket, client_address):
    handle = None
    while True:
        try:
            msg = client_socket.recv(BUFFER_SIZE).decode()
            if not msg:
                break
            response, file_transfer, filename = process_command(client_socket, msg, handle)
            if file_transfer:
                store_file(filename, client_socket, handle)
            else:
                client_socket.send(response.encode())
        except Exception as e:
            print(f"Error: {e}")
            break
    if handle and handle in clients:
        del clients[handle]
    client_socket.close()

def process_command(client_socket, msg, handle):
    parts = msg.split()
    command = parts[0]
    
    if command == "/register" and len(parts) == 2:
        return register_handle(parts[1], client_socket), False, None
    elif command == "/store" and len(parts) == 2:
        return f"Ready to receive {parts[1]}", True, parts[1]
    elif command == "/dir":
        return list_directory(), False, None
    elif command == "/get" and len(parts) == 2:
        return get_file(parts[1], client_socket), False, None
    elif command == "/leave":
        return "Connection closed. Thank you!", False, None
    elif command == "/?":
        return show_help(), False, None
    else:
        return "Error: Command not found or invalid parameters.", False, None

def register_handle(handle, client_socket):
    if handle in clients:
        return "Error: Registration failed. Handle or alias already exists."
    clients[handle] = client_socket
    return f"Welcome {handle}!"

def store_file(filename, client_socket, handle):
    if not handle:
        client_socket.send("Error: Please register a handle first.".encode())
        return
    
    filepath = os.path.join(DIRECTORY, filename)
    with open(filepath, "wb") as f:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            f.write(data)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    client_socket.send(f"{handle}<{timestamp}>: Uploaded {filename}".encode())

def list_directory():
    files = os.listdir(DIRECTORY)
    return "\n".join(files)

def get_file(filename, client_socket):
    filepath = os.path.join(DIRECTORY, filename)
    if not os.path.exists(filepath):
        return "Error: File not found in the server."
    
    with open(filepath, "rb") as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            client_socket.send(data)
    return f"File received from Server: {filename}"

def show_help():
    commands = [
        "/join <server_ip_add> <port>",
        "/leave",
        "/register <handle>",
        "/store <filename>",
        "/dir",
        "/get <filename>",
        "/?"
    ]
    return "\n".join(commands)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server started and listening on {SERVER_HOST}:{SERVER_PORT}")
    
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()