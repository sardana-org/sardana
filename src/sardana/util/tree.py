class BaseNode:
    
    def __init__(self, data):
        self.data = data

class BranchNode(BaseNode):
    
    def __init__(self, data):
        BaseNode.__init__(self, data)
        self.children = []

    def addChild(self, child):
        self.children.append(child)

class LeafNode(BaseNode):

    def __init__(self, data):
        BaseNode.__init__(self, data)

class Tree:

    def __init__(self, root):
        self._root = root
        
    def root(self):
        return self._root