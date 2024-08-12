class ObjectData:
    def __init__(self, guid: str, name: str, pos: tuple[float, float, float], size: tuple[float, float, float], tagId: int):
        self.guid_ = guid
        self.tagId_ = tagId
        self.name_ = name
        self.pos_ = list(pos)
        self.size_ = list(size)

    def guid(self):
        return self.guid_

    def tagId(self):
        return self.tagId_
    
    def name(self):
        return self.name_

    def pos(self):
        return self.pos_
    
    def x(self):
        return self.pos_[0]
    
    def y(self):
        return self.pos_[1]

    def z(self):
        return self.pos_[2]

    def size(self):
        return self.size_;

    def width(self):
        return self.size_[0]

    def height(self):
        return self.size_[1]

    def depth(self):
        return self.size_[2]

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
