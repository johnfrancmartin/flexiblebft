from enum import Enum


class MessageType(Enum):
    PROPOSE = 0
    VOTE = 1
    BLAME = 2

class Message:
    def __init__(self, type):
        self.type = type

class Proposal(Message):
    def __init__(self, block, view, previous_cert, status, leader, signature):
        self.block = block
        self.view = view
        self.previous_cert = previous_cert
        self.status = status
        self.leader = leader
        self.signature = signature
        super().__init__(MessageType.PROPOSE)

class Vote(Message):
    def __init__(self, block, view, signature, sender):
        self.block = block
        self.view = view
        self.signature = signature
        self.sender = sender
        super().__init__(MessageType.VOTE)

class Blame(Message):
    def __init__(self, view, sender, status):
        self.view = view
        self.sender = sender
        self.status = status
        super().__init__(MessageType.BLAME)
