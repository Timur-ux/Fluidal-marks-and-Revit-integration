from abc import ABCMeta, abstractmethod
from objectData import ObjectData
import json
import mariadb
import sys
from cache import Cache

class IDataBaseAdapter(metaclass=ABCMeta):

    @abstractmethod
    def getData(self, tagId: int) -> ObjectData:
        """
        Return objectData with corresponding tagId from DB or Cache
        If no Objects with this tagId None is returned
        """
        ...


    @abstractmethod
    def updateData(self, objectData):
        """
        Update objectData to DB/cache if it already exist there
        """   
        ...

    @abstractmethod
    def setData(self, objectData):
        """
        Add objectData to DB and cache
        """   
        ...


class MariaDBAdapter(IDataBaseAdapter):
    def __init__(self, configFileName, DBName = "objects", cacheSize = 100):
        assert configFileName.endswith(".json")
        self.cache = Cache(cacheSize)
        with open(configFileName, "r") as file:
            config = json.load(file)
        self.DBName = DBName
        try:
            self.connection = mariadb.connect(
                    user=config["user"],
                    password=config["password"],
                    host=config["host"],
                    port=config["port"],
                    database=config["database"]
                    )
        except mariadb.Error as e:
            print(f"Error: conneting to mariaDB failed: {e}")
            sys.exit(1)

        self.cursor = self.connection.cursor()
        
    def getData(self, tagId: int):
        if self.cache.isObjectInCache(tagId):
            return self.cache.getObjectData(tagId)
        
        self.cursor.execute(f"SELECT * FROM {self.DBName} WHERE tagid = {tagId};")
        items = list(iter(self.cursor))
        if len(items) == 0:
            return None
        if len(items) > 1:
            print("Warn: multiple items with same tagid in DB, first returned")
        item = items[0]
        return ObjectData(guid=item[0], name=item[1], tagId=item[5],\
                pos=(item[2], item[3], item[4]), size=(item[6], item[7], item[8]))

    def updateData(self, objectData):
        if self.cache.isObjectInCache(objectData.tagId()) \
        and self.cache.getObjectData(objectData.tagId()) == objectData:
            return
        
        self.cache.update(objectData)
        request = f"UPDATE {self.DBName} SET guid=?,name=?,x=?,y=?,z=?,width=?,height=?,depth=?,tagid=? WHERE tagid=?;"
        self.cursor.execute(request
                            , (objectData.guid()
                            , objectData.name()
                            , objectData.x()
                            , objectData.y()
                            , objectData.z()
                            , objectData.width()
                            , objectData.height()
                            , objectData.depth()
                            , objectData.tagId()
                            , objectData.tagId())
                            )
        self.connection.commit()

    def setData(self, objectData):
        self.cache.update(objectData)
        request = f"REPLACE INTO {self.DBName} SET guid=?,name=?,x=?,y=?,z=?,width=?,height=?,depth=?,tagid=?;"
        self.cursor.execute(request
                            , (objectData.guid()
                            , objectData.name()
                            , objectData.x()
                            , objectData.y()
                            , objectData.z()
                            , objectData.width()
                            , objectData.height()
                            , objectData.depth()
                            , objectData.tagId())
                            )
        self.connection.commit()


            

