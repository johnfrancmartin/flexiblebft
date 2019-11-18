from Block import Block
from time import time
from Certificate import Certificate
from MessageType import MessageType, Proposal, Vote, Blame
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

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

    def propose(self, steady_state, status):
        if status is None:
            status = {}
        if steady_state:
            # TODO: If steady_state, create block using Bk-1 as previously proposed value
            previous = Block(None, None, 0, 0, None)
            for sender, block in status.items():
                if block.view >= previous.view and block.height >= previous.height:
                    previous = block
        else:
            # TODO: Else create block using highest status cert as previously proposed value
            previous = self.locked
        if previous is not None:
            previous = previous.clone_for_view(self.view)
        height = 0
        if previous is not None:
            height = previous.height + 1
        block = self.protocol.create_block(height, self.view, previous)
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
                or (len(block.parent_hashes) > 0 and block.parent_hashes[-1] == hash(self.proposed)):
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
        if vote.view == self.view and block.height == self.proposed.height and block.id != self.proposed.id:
            # If same view, height and different ID
            self.blame()
            return
        elif vote.view == self.view and block.id not in self.blocks:
            self.blocks[block.id] = block
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
        highest = Block(None, None, 0, 0, None)
        for sender, block in proposal.status.items():
            if block.view >= highest.view and block.height >= highest.height:
                highest = block
        if highest.id is None or len(proposal.status) == 0 or hash(highest) in proposed.parent_hashes:
            return True
        else:
            return False

    def proposal_extends_previous(self, proposal):
        if hash(self.proposed) in proposal.block.parent_hashes:
            return True
        else:
            return False

    def broadcast(self, message):
        self.protocol.broadcast(self, message)

    def sign_blk(self, block):
        # Sign a message using the key
        signature = self.private_key.sign(str.encode(str(block.id)),
                                          padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                      salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256()
                                          )
        return signature
        # signature = self.private_key.sign(message, padding.PSS(mgf = padding.MGF1(hashes.SHA256()), salt_length = padding.PSS.MAX_LENGTH), hashes.SHA256())

    def verify_signature(self, block, signature, signer):
        decrypted = signer.public_key.decrypt(signature, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        return decrypted == str.encode(str(block.id))