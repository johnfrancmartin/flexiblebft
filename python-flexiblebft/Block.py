from Certificate import Certificate

class Block:
    def __init__(self, id, commands, height, view, parent_hashes):
        self.id = id
        self.commands = commands
        self.height = height
        self.view = view
        self.parent_hashes = parent_hashes
        if height > 0 and len(parent_hashes) == 0:
            raise NotImplementedError
        self.signatures = {}
        self.certification = None

    def clone_for_view(self, view):
        return Block(self.id, self.commands, self.height, view, self.parent_hashes)

    def __hash__(self):
        return hash(self.id)

    def sign(self, sender, signature):
        self.signatures[sender.id] = signature

    def certify(self):
        self.certification = Certificate(self, self.view, self.signatures)



class Certificate:
    def __init__(self, view, signatures):
        self.view = view
        self.signatures = signatures



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