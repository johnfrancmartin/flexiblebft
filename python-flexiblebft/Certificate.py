class Certificate:
    def __init__(self, block, view, signatures):
        self.block = block
        self.view = view
        self.signatures = signatures

# class Vote:
#     def __init__(self, replica, signature):
#         self.replica = replica
#         self.signature = signature