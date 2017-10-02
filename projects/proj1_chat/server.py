import sys
import socket
import select
from utils import * 

args = sys.argv

class Server(object):
    
    def __init__(self, port):
        self.socket = socket.socket()
        self.socket.bind(("", int(port)))
        self.socket.listen(5)
        self.socket_list = [self.socket]
        self.client_channels = {}   # client (socket)   => channel name
        self.channel_clients = {}   # channel name      => clients (sockets) 
        self.names = {}             # client (socket)   => client name
    
    def start(self):
        while True:
            ready_to_read,ready_to_write,in_error = select.select(self.socket_list,[],[],0)
            for s in ready_to_read:
                if s == self.socket:
                    sockfd, addr = self.socket.accept()
                    self.socket_list.append(sockfd)
                    name = sockfd.recv(MESSAGE_LENGTH)
                    while len(name.decode()) < MESSAGE_LENGTH:
                        name += sockfd.recv(MESSAGE_LENGTH)
                    self.names[sockfd] = name.strip()
                else:
                    try:
                        data = s.recv(MESSAGE_LENGTH)
                        if not data:
                            self.leave_channel(s, self.client_channels[s])
                            self.socket_list.remove(s)
                            
                        else:
                            while len(data.decode()) < MESSAGE_LENGTH:
                                data += s.recv(MESSAGE_LENGTH)
                            data_str = data.decode().strip()
                            data_words = data_str.split(" ")
                            if data_str.startswith("/join"):
                                if len(data_words) == 1:
                                    self.pad_and_send(s, SERVER_JOIN_REQUIRES_ARGUMENT)
                                else:
                                    channel_name = data_words[1]
                                    if channel_name not in self.channel_clients:
                                        self.pad_and_send(s, SERVER_NO_CHANNEL_EXISTS.format(channel_name))
                                    else:
                                        self.join_channel(s, channel_name)
                            elif data_str.startswith("/create"):
                                if len(data_words) == 1:
                                    self.pad_and_send(s, SERVER_CREATE_REQUIRES_ARGUMENT)
                                else:
                                    self.create_channel(s, data_words[1])
                            elif data_str.startswith("/list"):
                                self.list_channels(s)
                            elif data_str.startswith("/"):
                                print("in incorrect command case")
                                self.pad_and_send(s, SERVER_INVALID_CONTROL_MESSAGE.format(data_words[0]))
                            elif not self.client_channels[s]:
                                print("in client not in channel case")
                                self.pad_and_send(s, SERVER_CLIENT_NOT_IN_CHANNEL)
                            else:
                                msg_str = '[' + self.names[s] + '] ' + data.decode()
                                self.broadcast(s, msg_str.encode())
                    except:
                        self.broadcast(s, SERVER_CLIENT_LEFT_CHANNEL.format(self.names[s]))
                        continue


    def join_channel(self, client, channel):
        if client in self.client_channels:
            if self.client_channels[client] == channel:
                return
            else:
                self.leave_channel(client, self.client_channels[client])
        self.channel_clients[channel].append(client)
        self.client_channels[client] = channel
        self.broadcast(client, SERVER_CLIENT_JOINED_CHANNEL.format(self.names[client]))
        

    def leave_channel(self, client, channel):
        self.broadcast(client, SERVER_CLIENT_LEFT_CHANNEL.format(self.names[client]))
        self.channel_clients[channel].remove(client)
        del self.client_channels[client]


    def create_channel(self, client, channel):
        if channel in self.channel_clients:
            self.pad_and_send(client, SERVER_CHANNEL_EXISTS.format(channel))
        else:
            self.channel_clients[channel] = []
            self.join_channel(client, channel)


    def list_channels(self, client):
        msg = ""
        for channel in self.channel_clients.keys():
            msg += (channel + "\n")
        self.pad_and_send(client, msg)


    def broadcast(self, client, message):
        if client not in self.client_channels:
            self.pad_and_send(client, SERVER_CLIENT_NOT_IN_CHANNEL)
            return
        channel = self.client_channels[client]
        for s in self.channel_clients[channel]:
            if s != client:
                try:
                    self.pad_and_send(s, message)
                except:
                    s.close()
                    if s in self.socket_list:
                        self.socket_list.remove(s)


    def pad_message(self, message):
        while len(message) < MESSAGE_LENGTH:
            message += " "
        return message[:MESSAGE_LENGTH]


    def pad_and_send(self, client, message):
        client.sendall(self.pad_message(message))


if len(args) != 2:
    print("Please supply a port.")
    sys.exit()
server = Server(args[1])
server.start()