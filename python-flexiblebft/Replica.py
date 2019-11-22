from Block import Block
from time import time, sleep
from Certificate import Certificate
from MessageType import MessageType, Proposal, Vote, Blame
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature
from base64 import b64decode
import codecs

class Replica:
    def __init__(self, protocol, id, qr):
        # Replica Core
        self.protocol = protocol
        self.id = id
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        self.public_key = self.private_key.public_key()
        self.view = 0
        self.leader = False
        # Lock
        self.locked = None
        self.lock_time = None
        self.proposed = None
        # Blocks
        self.blocks = {}
        self.certified = []
        # Votes
        self.blames = {}
        self.changes = {}
        # Voting
        self.qr = qr
        # View Change
        self.blames = {}
        self.status = {}
        # Proposals
        self.proposals = []

    # REPLICA FUNCTIONS

    def view_change(self, status):
        self.changes[self.view] = time()
        self.status = {}
        self.proposed = None
        self.view += 1
        if self.id == self.view % self.protocol.n:
            self.leader = True
            self.propose(False, status)
        else:
            self.leader = False

    def create_block(self, previous):
        while len(self.protocol.commands_queue) == 0:
            print("SLEEP")
            sleep(0.1)
        commands = self.protocol.commands_queue.pop(0)
        previous_hash = None
        height = 0
        if previous is not None:
            previous_hash = previous.get_hash()
            height = previous.height + 1
        block = Block(commands, height, self.view, previous_hash)
        return block

    def propose(self, steady_state, status):
        if status is None:
            status = {}
        if steady_state:
            # TODO: If steady_state, create block using Bk-1 as previously proposed value
            previous = Block(None, 0, 0, None)
            for sender, block in status.items():
                if block.view >= previous.view and block.height >= previous.height:
                    previous = block
        else:
            # TODO: Else create block using highest status cert as previously proposed value
            previous = self.locked
        if previous is not None:
            previous = previous.clone_for_view(self.view)
        block = self.create_block(previous)
        proposal = Proposal(block, self.view, previous, status, self, self.sign_blk(block))
        self.broadcast(proposal)

    def receive_proposal(self, proposal):
        if proposal in self.proposals:
            return
        self.proposals.append(proposal)
        if proposal.view != self.view:
            # FAST FORWARD
            while proposal.view > self.view:
                self.view_change({self.id: self.locked})
        block = proposal.block
        if (self.proposed is None and self.proposal_extends_status(proposal)) \
                or (block.previous_hash is not None and block.previous_hash == self.proposed.get_hash()):
            self.proposed = block
            self.broadcast(proposal)
            self.vote(block)

    def vote(self, block):
        signature = self.sign_blk(block)
        # Conditionally Sign Block
        if self not in block.signatures:
            block.sign(self, signature)
            self.broadcast(Vote(block, self.view, signature, self))
        elif len(block.signatures) >= self.qr:
            block.sign(self, signature)
            self.broadcast(Vote(block, self.view, signature, self))
        if len(block.signatures) >= self.qr:
            self.lock(block)

    def receive_vote(self, vote):
        block = vote.block
        sender = vote.sender
        signature = vote.signature
        if not self.verify_signature(block, signature, sender):
            # If signature not valid, blame sender
            self.blame()
            return
        block_hash = block.get_hash()
        if vote.view == self.view and block.height == self.proposed.height and block_hash != self.proposed.get_hash():
            # If same view, height and different ID
            self.blame()
            return
        elif vote.view == self.view and block_hash not in self.blocks:
            self.blocks[block_hash] = block
        if len(block.signatures) >= self.qr:
            self.lock(block)

    def lock(self, block):
        if self.locked == block:
            return
        self.locked = block
        self.status[self.id] = block
        self.protocol.certify_block(block)
        if self.leader:
            self.propose(True, self.status)

    def blame(self):
        blame = Blame(self.view, self, self.locked)
        self.protocol.broadcast(self, blame)

    def receive_msg(self, message):
        if message.type == MessageType.PROPOSE:
            self.receive_proposal(message)
        elif message.type == MessageType.VOTE:
            self.receive_vote(message)
        elif message.type == MessageType.BLAME:
            self.receive_blame(message)

    def receive_blame(self, message):
        view = message.view
        sender = message.sender
        status = message.status
        if view not in self.blames:
            self.blames[view] = {sender.id: status}
        else:
            self.blames[view][sender.id] = status
        if len(self.blames[view]) >= self.qr:
            self.view_change(self.blames[view])

    def proposal_extends_status(self, proposal):
        proposed = proposal.block
        highest = Block(None, 0, 0, None)
        for sender, block in proposal.status.items():
            if block.view >= highest.view and block.height >= highest.height:
                highest = block
        if highest.commands is None or len(proposal.status) == 0 or highest.get_hash() == proposed.previous_hash:
            return True
        else:
            return False

    def proposal_extends_previous(self, proposal):
        if self.proposed.get_hash() == proposal.block.previous_hash:
            return True
        else:
            return False

    def broadcast(self, message):
        self.protocol.broadcast(self, message)

    def sign_blk(self, block):
        # Sign a message using the key
        hash_str = block.get_hash()
        signature = self.private_key.sign(str.encode(hash_str, 'utf-8'),
                                          padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                      salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256()
                                          )

        return signature

    def verify_signature(self, block, signature, signer):
        hash_str = block.get_hash()
        message = str.encode(hash_str, 'utf-8')
        try:
            signer.public_key.verify(
                signature,
                message,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature):
            return False
