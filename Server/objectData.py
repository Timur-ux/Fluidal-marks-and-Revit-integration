class ObjectData:
    def __init__(self, guid: str, tagId: int, markPos, name = None, objectPos = None, size = None, isPositional = False):
        self.guid = guid
        self.tagId = tagId
        self.name = name
        self.markPos = markPos
        self.objectPos = objectPos
        self.size = size
        self.isPositional = isPositional

    def mark2RevitTransform(self):
        """
            return homogeneous transformation 
            from mark coord system 
            to revit coord system
            (only for positional marks)
        """
        assert self.isPositional
        pass



