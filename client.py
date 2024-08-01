import socket
import os

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
BUFFER_SIZE = 1024

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    return client_socket

def store_file(client_socket, filename):
    if os.path.isfile(filename):
        client_socket.send(f"/store {filename}".encode())
        with open(filename, 'rb') as file:
            while True:
                data = file.read(BUFFER_SIZE)
                if not data:
                    break
                client_socket.sendall(data)
        client_socket.send(b'EOF')
        response = client_socket.recv(BUFFER_SIZE).decode()
        print(response)
    else:
        print("Error: File not found.\n")

def get_file(client_socket, filename):
    client_socket.send(f"/get {filename}".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()
    if response.startswith("Error"):
        print(response)
    else:
        with open(f"downloaded_{filename}", 'wb') as file:
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if data.endswith(b'EOF'):
                    file.write(data[:-3])
                    break
                file.write(data)
        print(f"File received from Server: {filename}\n")

def main():
    client_socket = None
    joined, registered = False, False

    while True:
        command = input("Enter command: ")
        command_parts = command.split()

        # check if command starts with '/'
        if not command.startswith('/'):
            print("Error: Command not found.\n")
            continue

        try:
            # '/?' 
            if command_parts[0] == '/?':
                if client_socket:
                    client_socket.send(command.encode())
                    print(client_socket.recv(BUFFER_SIZE).decode())
                else:
                    print("/join <server_ip_add> <port>\n/leave\n/register <handle>\n/store <filename>\n/dir\n/get <filename>\n/?")
            
            # '/join'
            elif command_parts[0] == '/join':
                if joined:
                    print("Error: Already connected to a server. Please leave the current server before joining a new one.\n")
                    continue
                if len(command_parts) < 3:
                    print("Error: Missing IP address or port number.\n")
                    continue
                if command_parts[1] == SERVER_HOST and command_parts[2] == str(SERVER_PORT):
                    try:
                        if client_socket:
                            client_socket.close()
                        client_socket = connect_to_server()
                        client_socket.send(command.encode())
                        response = client_socket.recv(BUFFER_SIZE).decode()
                        print(response)
                        if "successful" in response:
                            joined = True
                            registered = False
                    except (ConnectionRefusedError, ConnectionResetError, BrokenPipeError):
                        print("Error: Could not connect to the server. The server may be closed.\n")
                        if client_socket:
                            client_socket.close()
                        client_socket = None
                        joined, registered = False, False
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    print("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n")
        
            # '/register'
            elif joined and command_parts[0] == '/register':
                if registered:
                    print("Error: Handle already registered. You cannot register again.\n")
                    continue
                if len(command_parts) >= 2:
                    if joined:
                        client_socket.send(command.encode())
                        response = client_socket.recv(BUFFER_SIZE).decode()
                        print(response)
                        if "Welcome" in response:
                            registered = True
                    else:
                        print("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n")
                else:
                    print("Error: Command parameters do not match, missing, or is not allowed.\n")

            #  '/leave'
            elif joined and command_parts[0] == '/leave':
                if client_socket:
                    client_socket.send(command.encode())
                    print(client_socket.recv(BUFFER_SIZE).decode())
                    client_socket.close()
                    joined = False
                    registered = False
            
            # "/store"
            elif joined and registered and command_parts[0] == '/store':
                if len(command_parts) == 2:
                    store_file(client_socket, command_parts[1])
                else:
                    print("Error: Command parameters do not match, missing, or is not allowed.\n")
            
            # '/dir'
            elif joined and command_parts[0] == '/dir':
                if len(command_parts) == 1:
                    client_socket.send(command.encode())
                    response = client_socket.recv(BUFFER_SIZE).decode()
                    print(response)
            
            elif joined and command_parts[0] == '/get' and len(command_parts) == 2:
                get_file(client_socket, command_parts[1])

            # error message: client unregistered
            elif joined and command_parts[0] == '/store':
                if len(command_parts) == 2:
                    print("Error: Client must be registered to access this feature.\n")
                else:
                    print("Error: Client must be registered to access this feature.\n")

            # error messages: client unjoined
            elif not joined:
                if command_parts[0] == '/?':
                    print("/join <server_ip_add> <port>\n/leave\n/register <handle>\n/store <filename>\n/dir\n/get <filename>\n/?")
                elif command_parts[0] == '/leave':
                    print("Error: Disconnection failed. Please connect to the server first.\n")
                elif command_parts[0] == '/register':
                    print("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n")
                else:
                    print("Error: Connection to the Server has failed! Please check IP Address and Port Number.\n")
            
            # unknown command
            else:
                print("Error: Command not found.\n")

        except (ConnectionResetError, BrokenPipeError):
            print("Error: The server has been closed. You have been disconnected.\n")
            if client_socket:
                client_socket.close()
            client_socket = None
            joined, registered = False, False

if __name__ == "__main__":
    main()
