#!/usr/bin/evn python
# Netcat Replacement

import argparse
import sys
import socket
import subprocess
import threading

def arguement_parser():
    global parser 
    parser = argparse.ArgumentParser(description='Netcat Replacement')
    parser.add_argument('-l','--listen',action='store_true',help='listen on [host]:[port] for incoming connections')
    parser.add_argument('-e','--execute',type=str,help='execute the given file upon receiving a connection')
    parser.add_argument('-c','--command',action='store_true',help='initialize a command shell')
    parser.add_argument('-u','--upload',type=str,help='upon receiving connection upload a file and write to [destination]')
    parser.add_argument('-t','--target',type=str,help='target host')
    parser.add_argument('-p','--port',type=int,help='target port')
    args = parser.parse_args()
    return args

def client_sender(buffer):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        # connect to our target host
        client.connect((target,port))
        if len(buffer):
            client.send(buffer.encode())
        while True:
            # now wait for data back
            recv_len = 1
            response = ''
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode()
                if recv_len < 4096:
                    break
            print(response)
            # wait for more input
            buffer = input('')
            buffer += '\n'
            # send it off
            client.send(buffer.encode())
    except Exception as e:
        print(f'[*] Exception! Exiting. {e}')
        # tear down the connection
        client.close()

def server_loop():
    global port
    global target
    # if no target is defined, we listen on all interfaces
    if not len(target):
        target = '0.0.0.0'
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((target,port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        # spin off a thread to handle our new client
        client_thread = threading.Thread(target=client_handler,args=(client_socket,))
        client_thread.start()

def main():
    global execute
    global command
    global upload_destination

    args = arguement_parser()
    if not len(sys.argv[1:]):
        print(argparse.ArgumentParser.print_help(parser))
        exit(0)
    execute = args.execute
    command = args.command
    upload_destination = args.upload
    listen = args.listen
    port = args.port
    target = args.target

    try:
        if not listen and len(target) and port > 0:
            buffer = sys.stdin.read()
            client_sender(buffer)
    except:
        print(argparse.ArgumentParser.print_help(parser))

    if listen:
        server_loop()

def run_command(command):
    # trim the newline
    command = command.rstrip()
    # run the command and get the output back
    try:
        output = subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True)
    except:
        output = 'Failed to execute command.\r\n'
    # send the output back to the client
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command
    # check for upload
    if len(upload_destination):
        # read in all of the bytes and write to our destination
        file_buffer = ''
        # keep reading data until none is available
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data.decode()
        # now we take these bytes and try to write them out
        try:
            file_descriptor = open(upload_destination,'wb')
            file_descriptor.write(file_buffer.encode())
            file_descriptor.close()
            # acknowledge that we wrote the file out
            client_socket.send(f'Successfully saved file to {upload_destination}\r\n'.encode())
        except:
            client_socket.send(f'Failed to save file to {upload_destination}\r\n'.encode())
    # check for command execution
    if len(execute):
        # run the command
        output = run_command(execute)
        client_socket.send(output.encode())
    # now we go into another loop if a command shell was requested
    if command:
        while True:
            # show a simple prompt
            client_socket.send('<BHP:#> '.encode())
            # now we receive until we see a linefeed (enter key)
            cmd_buffer = ''
            while '\n' not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024).decode()
            # send back the command output
            response = run_command(cmd_buffer)
            # send back the response
            client_socket.send(response.encode())

if __name__ == '__main__':
    main()
    