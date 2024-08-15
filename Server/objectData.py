class ObjectData:
    def __init__(self, guid: str, name: str, pos: tuple[float, float, float], rotation: tuple[float, float, float], size: tuple[float, float, float], tagId: int, isPositional = False):
        self.guid_ = guid
        self.tagId_ = tagId
        self.name_ = name
        self.pos_ = pos
        self.size_ = size
        self.rotation_ = rotation
        self.isPositional_ = isPositional

    def guid(self):
        return self.guid_

    def tagId(self):
        return self.tagId_
    
    def name(self):
        return self.name_

    def pos(self):
        return self.pos_

    def rotation(self):
        return self.rotation_
    
    def x(self):
        x, y, z = self.pos_
        return x

    def isPositional(self):
        return self.isPositional_
    
    def y(self):
        x, y, z = self.pos_
        return y

    def z(self):
        x, y, z = self.pos_
        return z

    def size(self):
        return self.size_;

    def width(self):
        w, h, d = self.size_
        return w

    def height(self):
        w, h, d = self.size_
        return h

    def depth(self):
        w, h, d = self.size_
        return d

    def __eq__(self, other):
        res = \
        self.guid() == other.guid() and \
        self.name() == other.name() and \
        self.x() == other.x() and \
        self.y() == other.y() and \
        self.z() == other.z() and \
        self.width() == other.width() and \
        self.height() == other.height() and \
        self.depth() == other.depth()

        return res
