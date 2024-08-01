import socket
import threading
import os
from datetime import datetime

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024
FILE_DIR = 'Server Directory'

# ensure file directory exists
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR) 

# store client aliases
aliases = {}

def handle_client(client_socket, addr):
    print(f"[+] {addr} connected.")
    joined = False
    registered = False
    while True:
        try:
            # receive message from client
            message = client_socket.recv(BUFFER_SIZE).decode()
            if not message:
                break
            print(f"Received message: {message}")  # Debug print
            command = message.strip().split()
            print(f"Parsed command: {command}")  # Debug print

            # error message: check if command starts with '/'
            if not message.startswith('/'):
                client_socket.send("Error: Command not found.\n".encode())
                continue
            
            # '/?'
            if command[0] == '/?':
                handle_help(client_socket)

            # '/join'
            elif command[0] == '/join' and len(command) == 3:
                if len(command) == 3:
                    # must be '/join 127.0.0.1 12345' to successfully join 
                    if command[1] == SERVER_HOST and command[2] == str(SERVER_PORT):
                        joined = True
                        client_socket.send("Connection to the File Exchange Server is successful!\n".encode())
                    # error: faulty params
                    else:
                        client_socket.send("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n".encode())
                else:
                    client_socket.send("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n".encode())
            
            # '/register <handle>'
            elif joined and command[0] == '/register':
                if len(command) >= 2:
                    handle_register(client_socket, command[1])
                    registered = True
                else:
                    client_socket.send("Error: Command parameters do not match, missing, or is not allowed.\n".encode())
            # '/leave'
            elif joined and command[0] == '/leave' and len(command) == 1:
                client_socket.send("Connection closed. Thank you!\n".encode())
                client_socket.close()
                break

            # "/store <filename>""
            elif joined and registered and command[0] == '/store':
                if len(command) == 2:
                    handle_store(client_socket, command[1])
                else:
                    client_socket.send("Error: Command parameters do not match, missing, or is not allowed.\n".encode())
            # "/dir"
            elif joined and registered and command[0] == '/dir' and len(command) == 1:
                handle_dir(client_socket)
            # "/get <filename>""
            elif joined and registered and command[0] == '/get':
                if len(command) == 2:
                    handle_get(client_socket, command[1])
                else:
                     client_socket.send("Error: Command parameters do not match, missing, or is not allowed.\n".encode())            # error message: client unregistered
            elif joined and not registered: 
                if command[0] == '/store' and len(command) == 2:
                    client_socket.send("Error: Client must be registered to access this feature.\n".encode())
                elif command[0] == '/dir':
                    client_socket.send("Error: Client must be registered to access this feature.\n".encode())
                elif command[0] == '/get':
                    client_socket.send("Error: Client must be registered to access this feature.\n".encode())
                else:
                    client_socket.send("Error: Client must be registered to access this feature.\n".encode())
            # error messages: client unjoined
            elif not joined:
                if command[0] == '/?':
                    handle_help(client_socket)
                elif command[0] == '/leave':
                    client_socket.send("Error: Disconnection failed. Please connect to the server first.\n")
                elif command[0] == '/register':
                    client_socket.send("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n".encode())
                else:
                    client_socket.send("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n".encode()) 
            else:
                client_socket.send("Error: Command not found.\n".encode())

        except Exception as e:
            print(f"[-] Error: {str(e)}")
            client_socket.close()
            break

# '/?'
def handle_help(client_socket):
    help_message = "/join <server_ip_add> <port>\n/leave\n/register <handle>\n/store <filename>\n/dir\n/get <filename>\n/?\n"
    client_socket.send(help_message.encode())

# '/register <handle>'
def handle_register(client_socket, handle):
    if handle in aliases.values():
        client_socket.send("Error: Registration failed. Handle or alias already exists.\n".encode())
    else:
        aliases[client_socket] = handle
        client_socket.send(f"Welcome {handle}!\n".encode())

# '/store <filename>'
def handle_store(client_socket, filename):
    file_path = os.path.join(FILE_DIR, filename)
    with open(file_path, 'wb') as file:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if data.endswith(b'EOF'):
                file.write(data[:-3])
                break
            file.write(data)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    handle = aliases.get(client_socket)                       
    client_socket.send(f"{handle} <{timestamp}>: Uploaded {filename}\n".encode())

# '/dir'
def handle_dir(client_socket):
    try:
        files = os.listdir(FILE_DIR)
        if files:
            file_list = "\n".join(files)
            client_socket.send(f"Server Directory\n{file_list}\n".encode())
        else:
            client_socket.send("Server Directory is empty.\n".encode())
    except Exception as e:
        client_socket.send(f"Error: {str(e)}\n".encode())
    
# '/get <filename>'
def handle_get(client_socket, filename):
    file_path = os.path.join(FILE_DIR, filename)
    if os.path.isfile(file_path):
        client_socket.send(f"Starting file transfer: {filename}\n".encode())
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                client_socket.sendall(data)
        client_socket.send(b'EOF')
    else:
        client_socket.send("Error: File not found in the server.\n".encode())

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()

if __name__ == "__main__":
    main()
