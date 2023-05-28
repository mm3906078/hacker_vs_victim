#!/usr/bin/env python3

import socket
import threading
import random
import time
import json
import os

# data structure for communication with the server
# {
#     'client_id': client_id,
#     'hostname': hostname,
#     'socket': new_client_socket,
#     'address': new_client_address,
#     'last_ping': time.time(),
#     'main': False
# }
SERVER_ADDRESS = '192.168.1.10'
SERVER_PORT = 12345
BUFFER_SIZE = 1024
PING_PORT = 12344

def connect_to_server():
    # Create the client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((SERVER_ADDRESS, SERVER_PORT))
    print(f'Connected to server {SERVER_ADDRESS}:{SERVER_PORT}')

    # Receive the new port number from the server
    new_port = client_socket.recv(BUFFER_SIZE)
    new_port = int(new_port.decode())
    print(f'New port: {new_port}')

    # close the client socket
    client_socket.close()

    # Connect to the new port
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((SERVER_ADDRESS, new_port))
    print(f'Connected to server {SERVER_ADDRESS}:{new_port}')

    # Send the hostname to the server
    hostname = socket.gethostname()
    data_socket.sendall(hostname.encode())

    # Receive the client id from the server
    client_id = data_socket.recv(BUFFER_SIZE)
    client_id = int(client_id.decode())
    print(f'Client id: {client_id} received from server')

    # append the main client socket to the list
    a = {'hostname': hostname, 'socket': data_socket, 'address': (SERVER_ADDRESS, new_port), 'client_id': client_id, 'main': True}
    return a

    # close the data socket
    # data_socket.close()

def ping_server(a):
    while True:
        # Create the client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        client_socket.connect((SERVER_ADDRESS, PING_PORT))
        print(f'Connected to server {SERVER_ADDRESS}:{PING_PORT} for ping')

        # Send the client id to the server to ping
        # print(f'Sending client id {all_connections[0]["client_id"]} to server')
        client_socket.sendall(str(a['client_id']).encode())

        # close the client socket
        client_socket.close()

        time.sleep(5)

def handle_client(client_socket):
    # wait for server to send the new instructions
    while True:
        data = client_socket.recv(BUFFER_SIZE)
        if not data:
            break
        print(f'Received data: {data.decode()}')
# Get the data from the server
# {instruction: 'download_file', filepath: 'C:\\Users\\user\\Desktop\\test.txt'}
# Send the data to the server
# {instruction: 'ok', file_size: 1234}`
        data = data.decode()
        data = json.loads(data)
        if data['instruction'] == 'download_file':
            # check if file exists
            if os.path.isfile(data['filepath']):
                # find file size
                file_size = os.path.getsize(data['filepath'])
                # send file size & ok to server
                client_socket.sendall(f"instruction: 'ok', file_size: {file_size}".encode())
                # send file to server
                print(f'Sending file {data["filepath"]} to server ...')
                with open(data['filepath'], 'rb') as f:
                    bytes_to_send = f.read(BUFFER_SIZE)
                    while bytes_to_send:
                        client_socket.sendall(bytes_to_send)
                        bytes_to_send = f.read(BUFFER_SIZE)
            else:
                # send error to server
                client_socket.sendall(f"instruction: 'error', message: 'file not found'".encode())
        else:
            # send error to server
            client_socket.sendall(f"instruction: 'error', message: 'unknown instruction'".encode())


def main():
    # Connect to the server
    data = connect_to_server()

    # create thread for pinging the server
    ping_thread = threading.Thread(target=ping_server, args=(data,))
    ping_thread.start()

    handle_client(data['socket'])


if __name__ == '__main__':
    main()

