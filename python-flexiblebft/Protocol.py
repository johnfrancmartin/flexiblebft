import math
import random
from threading import Thread
from Block import Block
from Replica import Replica
from MessageType import MessageType
from time import sleep


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
            print(sender.id, "PROPOSED", message.block.id)
        elif message.type is MessageType.VOTE:
            print(sender.id, "VOTED FOR", message.block.id)
        else:
            print(sender.id, "BLAMED IN", message.view)

    def send_msg(self, replica, message):
        sleep(random.random())
        replica.receive_msg(message)

    def create_block(self, height, view, previous):
        while len(self.commands_queue) == 0:
            print("SLEEP")
            sleep(0.1)
        commands = self.commands_queue.pop(0)
        parent_hashes = []
        if previous is not None:
            parent_hashes = previous.parent_hashes + [hash(previous)]
        block = Block(self.block_index, commands, height, view, parent_hashes)
        self.block_index += 1
        print(self.block_index)
        return block

    def certify_block(self, block):
        print("CERTIFIED:", str(block.id))

    def add_command(self, command):
        self.commands.append(command)
        self.commands_queue.append(command)



