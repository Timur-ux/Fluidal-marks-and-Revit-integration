from objectData import ObjectData
from queue import Queue
from typing import Optional

class Cache:
    """Cache for detected tags"""
    def __init__(self, cacheSize = 100):
        assert cacheSize > 0
        self.cache: dict[int, ObjectData] = {}
        self.cacheQueue: Queue[int] = Queue(maxsize = cacheSize)

    def update(self, objectData):
        """
        update objectData if it already in cache,
        add it to cache otherwise
        """
        if objectData.tagId() not in self.cache:
            if self.cacheQueue.full():
                lastId = self.cacheQueue.get()
                del self.cache[lastId]
            self.cacheQueue.put(objectData.tagId())


        self.cache[objectData.tagId()] = objectData


    def isObjectInCache(self, tagId) -> bool:
        return tagId in self.cache

    def getObjectData(self, tagId: int) -> Optional[ObjectData]:
        if tagId not in self.cache:
            return None
        return self.cache[tagId]
