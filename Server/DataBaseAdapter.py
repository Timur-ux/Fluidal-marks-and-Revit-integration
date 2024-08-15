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
    def __init__(self, configFileName, DBName = "objects", positionalMarksDBName = "positionalMarks", cacheSize = 100):
        assert configFileName.endswith(".json")
        self.cache = Cache(cacheSize)
        with open(configFileName, "r") as file:
            config = json.load(file)
        self.objectsDBName = DBName
        self.positionalMarksDBName = positionalMarksDBName
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
        '''
            First try to fetch data from objectsDB
            If there not exist -- try to fetch data from positionalMarksDB
            If there not exist -- return None
        '''
        if self.cache.isObjectInCache(tagId):
            return self.cache.getObjectData(tagId)

        self.cursor.execute(f"SELECT * FROM {self.objectsDBName} WHERE tagid = {tagId};")
        isPositional = False

        items = list(iter(self.cursor))
        if len(items) == 0:
            isPositional = True
            self.cursor.execute(f"SELECT * FROM {self.positionalMarksDBName} WHERE tagid = {tagId};")
            items = list(iter(self.cursor))
            if len(items) == 0:
                return None
        if len(items) > 1:
            print("Warn: multiple items with same tagid in DB, first returned")
        item = items[0]
        tvec = tuple(json.loads(item[6]))
        rvec = tuple(json.loads(item[7]))

        result = ObjectData(guid=item[0], name=item[1], tagId=item[5],\
                pos=tvec, rotation=rvec, size=(item[3], item[4], item[5]), isPositional=isPositional)
        self.cache.update(result)
        return result;

    def updateData(self, objectData):
        if self.cache.isObjectInCache(objectData.tagId()) \
        and self.cache.getObjectData(objectData.tagId()) == objectData:
            return
        
        self.cache.update(objectData)
        tvecs = json.dumps(objectData.pos())
        rvecs = json.dumps(objectData.rotation())
        if objectData.isPositional():
            request = f"UPDATE {self.positionalMarksDBName} SET guid=?,tvecs=?, rvecs=?, tagid=? WHERE tagid=?;"
            self.cursor.execute(request
                                , (objectData.guid()
                                , tvecs
                                , rvecs
                                , objectData.tagId()
                                , objectData.tagId())
                                )
        else:
            request = f"UPDATE {self.objectsDBName} SET guid=?,name=?,tvecs=?, rvecs=?,width=?,height=?,depth=?,tagid=? WHERE tagid=?;"
            self.cursor.execute(request
                                , (objectData.guid()
                                , objectData.name()
                                , tvecs
                                , rvecs
                                , objectData.width()
                                , objectData.height()
                                , objectData.depth()
                                , objectData.tagId()
                                , objectData.tagId())
                                )
        self.connection.commit()

    def setData(self, objectData):
        self.cache.update(objectData)
        tvecs = json.dumps(objectData.pos())
        rvecs = json.dumps(objectData.rotation())
        if objectData.isPositional():
            request = f"REPLACE INTO {self.positionalMarksDBName} SET guid=?,tvecs=?,rvecs=?,tagid=?;"
            self.cursor.execute(request
                                , (objectData.guid()
                                , tvecs
                                , rvecs
                                , objectData.tagId())
                                )
        else:
            request = f"REPLACE INTO {self.objectsDBName} SET guid=?,name=?,tvecs=?, rvecs=?,width=?,height=?,depth=?,tagid=?;"
            self.cursor.execute(request
                                , (objectData.guid()
                                , objectData.name()
                                , tvecs
                                , rvecs
                                , objectData.width()
                                , objectData.height()
                                , objectData.depth()
                                , objectData.tagId())
                                )
        self.connection.commit()


            

