import math
import random
import traceback
from threading import Thread
import socket
from Block import Block
from Replica import Replica
from MessageType import MessageType
from time import sleep
from CONFIG import PROTOCOL_HOST, PROTOCOL_PORT
from SocketHelper import recvMsg, sendMsg, SocketDisconnectedException

class Protocol:
    def __init__(self, n):
        # Initialization
        self.replicas = []
        self.n = n
        self.f = math.ceil(n/2) # max-f for now
        self.qr = self.f + 1
        # Runtime Attributes
        self.leader_index = 0
        self.block_index = 0
        self.delta = 10 # seconds
        self.commands_queue = []
        self.commands = []
        for i in range(0, self.n):
            self.replicas.append(Replica(self, i, self.qr))
        # Connection
        self.local_sock = self.listen_socket_init('', PROTOCOL_PORT)  # 44444

    def initialize_connection(self):

        if self.local_sock:
            print("Local Listening Socket Established; Host:", '; Port:', PROTOCOL_PORT)

    def run(self):
        leader = self.replicas[0]
        leader.leader = True
        leader.propose(False, {})

    def broadcast(self, sender, signed_msg):
        self.print_broadcast(sender, signed_msg)
        workers = []
        for replica in self.replicas:
            x = Thread(target=self.send_msg, args=(replica, signed_msg,))
            x.start()
            workers.append(x)
        for worker in workers:
            worker.join()

    def print_broadcast(self, sender, message):
        if message.type is MessageType.PROPOSE:
            print(sender.id, "PROPOSED", message.block.get_hash())
        elif message.type is MessageType.VOTE:
            print(sender.id, "VOTED FOR", message.block.get_hash())
        else:
            print(sender.id, "BLAMED IN", message.view)

    def send_msg(self, replica, message):
        sleep(random.random())
        replica.receive_msg(message)

    def certify_block(self, block):
        print("CERTIFIED:", block.get_hash())

    def add_command(self, command):
        self.commands.append(command)
        self.commands_queue.append(command)



    def listen_socket_init(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen(10)
            return sock
        except Exception as e:
            print(e)

    def receive_client(self, client_socket, addr):
        while True:
            try:
                # bft_proto.BlameMSG()
                # bft_proto.ProposalMSG()
                # bft_proto.VoteMSG()
                # msg = recvMsg(client_socket, bft_proto.BlameMSG())
                msg = "NOT IMPLEMENTED YET"
                print("recv replica request: ", str(msg))
                # processA2U(msg, self)
            except SocketDisconnectedException as e:
                print("[ERROR: UPS SOCKET DISCONNECTED. RECONNECTING...]")
                # self.ups_sock, addr = self.connection.local_sock.accept()
                pass
            except Exception as e:
                print("ERROR: Listen for Replicas Thread.", e)
                print("Stack Trace:", traceback.print_exc())
                pass
            # msg = client_socket.recv(1024)
            #
            # client_socket.send(msg)
        # clientsocket.close()

    def listen_to_replicas(self):
        while True:
            c, address = self.local_sock.accept()  # Establish connection with client.
            x = Thread(target=self.receive_client, args=(c, address))
            x.start()
        # self.local_sock.close()

