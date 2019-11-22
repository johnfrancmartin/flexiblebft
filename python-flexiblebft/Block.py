from Certificate import Certificate
import hashlib

class Block:
    def __init__(self, commands, height, view, previous_hash):
        self.commands = commands
        self.height = height
        self.view = view
        self.previous_hash = previous_hash
        if height > 0 and previous_hash is None:
            raise NotImplementedError
        self.signatures = {}
        self.certification = None

    def clone_for_view(self, view):
        return Block(self.commands, self.height, view, self.previous_hash)

    def get_hash(self):
        previous = self.previous_hash
        if previous is None:
            previous = ""
        commands_str = " ".join([str(i) for i in self.commands])
        hash_str = commands_str + ":" + str(self.view) + ":" + str(self.height) + ":" + previous
        hash_bytes = str.encode(hash_str)
        return hashlib.sha256(hash_bytes).hexdigest()

    def sign(self, sender, signature):
        self.signatures[sender.id] = signature

    def certify(self):
        self.certification = Certificate(self, self.view, self.signatures)



# class Block {
#     friend HotStuffCore;
#     std::vector<uint256_t> parent_hashes;
#     std::vector<uint256_t> cmds;
#     quorum_cert_bt qc;
#     uint256_t qc_ref_hash;
#     bytearray_t extra;
#
#     /* the following fields can be derived from above */
#     uint256_t hash;
#     std::vector<block_t> parents;
#     block_t qc_ref;
#     quorum_cert_bt self_qc;
#     uint32_t height;
#     bool delivered;
#     int8_t decision;
#
#     std::unordered_set<ReplicaID> voted;