import sys
import socket
import select
from utils import *

class Client(object):

    def __init__(self, name, address, port):
        self.name = name
        self.address = address
        self.port = int(port)
        self.socket = socket.socket()

    def start(self):
        try:
            self.socket.connect((self.address, self.port))
            self.send(self.name)
            sys.stdout.write(CLIENT_MESSAGE_PREFIX); sys.stdout.flush()
        except:
            print(CLIENT_CANNOT_CONNECT.format(self.address, self.port)) 
            sys.exit() 
        while True:
            socket_list = [sys.stdin, self.socket]
            ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [], 0)
            for s in ready_to_read:
                if s == self.socket:
                    data = s.recv(MESSAGE_LENGTH)
                    if not data:
                        sys.stdout.write(CLIENT_WIPE_ME)
                        print(CLIENT_SERVER_DISCONNECTED.format(self.address, self.port))
                        sys.exit()
                    while len(data.decode()) < MESSAGE_LENGTH:
                        data += s.recv(MESSAGE_LENGTH)
                    sys.stdout.write(CLIENT_WIPE_ME)
                    if len(data.decode().strip()) == 0:
                        sys.stdout.write("\r" + data.decode().strip())
                    else:
                        sys.stdout.write("\r" + data.decode().strip() + "\n")
                    sys.stdout.write(CLIENT_MESSAGE_PREFIX); sys.stdout.flush()
                else:
                    msg = sys.stdin.readline()
                    self.send(msg)
                    sys.stdout.write(CLIENT_MESSAGE_PREFIX); sys.stdout.flush()


    def send(self, message):
        self.socket.sendall(self.pad_message(message))

    def pad_message(self, message):
        while len(message) < MESSAGE_LENGTH:
            message += " "
        return message[:MESSAGE_LENGTH]

args = sys.argv
if len(args) != 4:
    print("Please supply a server address and port.")
    sys.exit()
client = Client(args[1], args[2], args[3])
client.start()