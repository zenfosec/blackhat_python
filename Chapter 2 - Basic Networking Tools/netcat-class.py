#!/usr/bin/env python
# Netcat Replacement (with OOP)

import argparse
import sys
import socket
import subprocess
import threading

def argument_parser(args=None):
    parser = argparse.ArgumentParser(description="Blackhat Python Netcat", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-c", "--command", action="store_true", help="command shell")
    parser.add_argument("-e", "--execute", help="execute specified file")
    parser.add_argument("-l", "--listen", action="store_true", help="listen")
    parser.add_argument("-p", "--port", type=int, default=5555, help="specified port")
    parser.add_argument("-t", "--target", default="0.0.0.0")
    parser.add_argument("-u", "--upload", help="upload file")

    args = parser.parse_args()
    if not sys.argv[1:]:
        parser.print_help()
        sys.exit(1)
    return args

class Netcat:
    def __init__(self, args=None):
        self.args = argument_parser(args)
        self.target = self.args.target
        self.port = self.args.port
        self.listen = self.args.listen
        self.command = self.args.command
        self.upload = self.args.upload
        self.execute = self.args.execute
        self.buffer = ""

    def client_sender(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # connect to our target host
            client.connect((self.target, self.port))
            if len(self.buffer):
                client.send(self.buffer.encode())
            while True:
                # now wait for data back
                recv_len = 1
                response = ""
                while recv_len:
                    data = client.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                print(response, end="")
                # wait for more input
                self.buffer = input("")
                self.buffer += "\n"
                # send it off
                client.send(self.buffer.encode())
        except:
            print("[*] Exception! Exiting.")
            # tear down the connection
            client.close()

    def server_loop(self):
        if not self.target:
            self.target = "0.0.0.0"
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.target, self.port))
        server.listen(5)
        while True:
            client_socket, addr = server.accept()
            # spin off a new thread to handle the client
            client_thread = threading.Thread(target=self.client_handler, args=(client_socket,))
            client_thread.start()

    def run_command(self, command):
        # trim the newline
        command = command.rstrip()
        # run the command and get the output back
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except:
            output = b"Failed to execute command.\r\n"
        # send the output back to the client
        return output

    def client_handler(self, client_socket):
        if self.execute:
            # run the command
            output = self.run_command(self.execute)
            client_socket.send(output)
        if self.command:
            while True:
                # show a simple prompt
                client_socket.send(b"<nc:#> ")
                # now we receive until we see a linefeed (enter key)
                cmd_buffer = b""
                while "\n" not in cmd_buffer.decode():
                    cmd_buffer += client_socket.recv(1024)
                # send back the command output
                response = self.run_command(cmd_buffer.decode())
                # send back the response
                client_socket.send(response)

    def run(self):
        if self.listen:
            self.server_loop()
        else:
            if len(self.target) and self.port > 0:
                buffer = sys.stdin.read()
                self.client_sender(buffer)
            if self.upload:
                file_buffer = sys.stdin.read()
                self.client_sender(file_buffer)
            if self.execute:
                self.client_sender()
            if self.command:
                self.client_sender()

if __name__ == "__main__":
    args=argument_parser()
    nc = Netcat(args)
    nc.run()