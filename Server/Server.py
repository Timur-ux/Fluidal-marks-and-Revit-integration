import zmq
import json
from math import sqrt
from DataBaseAdapter import IDataBaseAdapter, MariaDBAdapter
from objectData import ObjectData

EVALUATION_ERROR = 0.05

def isObjectMoved(oldPos: tuple[float, float, float], curPos: tuple[float, float, float]):
    sumOfSquares = 0
    for old, new in zip(oldPos, curPos):
        sumOfSquares += (old - new)**2
    
    difference = sqrt(sumOfSquares)

    return difference > EVALUATION_ERROR

def notifyRevitAboutMovedObject(oldObjectData, newObjectData, revitSocket):
    x0,y0,z0 = oldObjectData.pos()
    x, y, z = newObjectData.pos()

    data = {
            "guid" : newObjectData.guid(),
            "dx" : x - x0,
            "dy" : y - y0,
            "dz" : z - z0
            }
    print(json.dumps(data))
    
    revitSocket.send_string(json.dumps(data))
    

class Server:
    def __init__(self, context, serverSocket, revitSocket, dbAdapter: IDataBaseAdapter):
        self.context = context
        
        self.socket = context.socket(zmq.PULL)
        self.socket.connect(serverSocket)
        
        self.revitSocket = context.socket(zmq.PUSH)
        self.revitSocket.connect(revitSocket)

        self.dbAdapter = dbAdapter

    def processDetectedMark(self, data):
        tagId, x, y, z, w, h, d = data["id"], data["x"], data["y"], data["z"],\
                data["width"], data["height"], data["depth"]


        objectData = self.dbAdapter.getData(tagId)
        assert objectData is not None

        oldPos = (objectData.x(),objectData.y(), objectData.z())
        if isObjectMoved(oldPos, (x, y, z)):
            newObjectData = ObjectData(guid=objectData.guid(), name=objectData.name(), tagId=tagId, pos=(x, y, z), size=(w, h, d))
            self.dbAdapter.updateData(newObjectData)
            notifyRevitAboutMovedObject(objectData, newObjectData, self.revitSocket)

    def processPostElementData(self, data):
        objectData = ObjectData(guid=data['guid'], name=data['name'], tagId=data['fluidalMarkId'], \
                pos=(data["x"], data["y"], data["z"]), \
                size=(data["width"], data["height"], data["depth"]))
        self.dbAdapter.setData(objectData)

    def process(self, message):
        data = json.loads(message)
        print(data)
        if data["type"] == "DetectedMark":
            self.processDetectedMark(data)
        elif data["type"] == "PostElementData":
            self.processPostElementData(data);

        
    
    def startProccessing(self):
        print("Message proccessing started")
        while True:
            message = self.socket.recv()
            self.process(message)
