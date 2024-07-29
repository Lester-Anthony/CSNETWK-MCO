import socket
import threading
import os

BUFFER_SIZE = 1024
client_socket = None
connected = False

def receive_messages():
    global client_socket
    while True:
        try:
            msg = client_socket.recv(BUFFER_SIZE).decode()
            if not msg:
                break
            print(msg)
        except Exception as e:
            print(f"Error: {e}")
            break
    client_socket.close()

def send_command(command):
    global client_socket, connected
    parts = command.split()
    cmd = parts[0]

    if cmd == "/join" and len(parts) == 3:
        if connected:
            print("Already connected to a server. Use /leave to disconnect first.")
        else:
            connect_to_server(parts[1], int(parts[2]))
    elif cmd == "/leave":
        if connected:
            client_socket.send(command.encode())
            connected = False
            print("Connection closed. Thank you!")
        else:
            print("Error: Disconnection failed. Please connect to the server first.")
    elif not connected:
        print("Error: Please connect to the server first using /join <server_ip_add> <port>")
    else:
        if cmd == "/store" and len(parts) == 2:
            filename = parts[1]
            if os.path.exists(filename):
                print("File Found!!!")
                client_socket.send(command.encode())
                with open(filename, "rb") as f:
                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break
                        client_socket.send(data)
                client_socket.send(b"")  # Indicate the end of file transfer
            else:
                print("Error: File not found.")
        else:
            client_socket.send(command.encode())

def connect_to_server(server_ip, port):
    global client_socket, connected
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, port))
        connected = True
        print("Connection to the File Exchange Server is successful!")
        receive_thread = threading.Thread(target=receive_messages)
        receive_thread.start()
    except Exception as e:
        print(f"Error: Connection to the Server has failed! Please check IP Address and Port Number. ({e})")

def main():
    while True:
        command = input("Enter command: ")
        send_command(command)
        if command == "/leave":
            break

if __name__ == "__main__":
    main()
