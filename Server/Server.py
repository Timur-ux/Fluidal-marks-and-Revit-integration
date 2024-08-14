import zmq
import json
from math import sqrt
from DataBaseAdapter import IDataBaseAdapter, MariaDBAdapter
from objectData import ObjectData
import numpy as np

EVALUATION_ERROR = 0.05

def isObjectMoved(oldPos: tuple[float, float, float], curPos: tuple[float, float, float]):
    sumOfSquares = 0
    for old, new in zip(oldPos, curPos):
        sumOfSquares += (old - new)**2
    
    difference = sqrt(sumOfSquares)

    return difference > EVALUATION_ERROR

def notifyRevitAboutMovedObject(guid, newPos, newRot, revitSocket):
    data = json.dumps({
            "guid" : guid,
            "newPos" : newPos,
            "newRot" : newRot
            })

    print(data)
    
    revitSocket.send_string(data)
    

class Server:
    def __init__(self, context, serverSocket, revitSocket, dbAdapter: IDataBaseAdapter):
        self.context = context
        
        self.socket = context.socket(zmq.PULL)
        self.socket.connect(serverSocket)
        
        self.revitSocket = context.socket(zmq.PUSH)
        self.revitSocket.connect(revitSocket)

        self.dbAdapter = dbAdapter

        # Костыль
        self.cameraPosition = None
        self.cameraRot = None

    def processDetectedMark(self, data):
        tagId, pos, rot = data["id"], tuple(data["pos"]), tuple(data["rot"])


        objectData = self.dbAdapter.getData(tagId)
        if objectData is None:
            print(f"Mark not placed in DB detected. Tag id: {tagId}. Skipping...")
            return
        if objectData.isPositional():
            self.cameraPosition = tuple(np.asarray(pos) + np.asarray(objectData.pos()))
            self.cameraRot = rot
            return

        oldPos = objectData.pos()
        if isObjectMoved(oldPos, pos):
            objectData.pos_ = pos
            objectData.rotation_ = rot
            self.dbAdapter.updateData(objectData)
            notifyRevitAboutMovedObject(objectData.guid(), pos, rot, self.revitSocket)

    def processPostElementData(self, data):
        if data["isPositional"]:
            objectData = ObjectData(guid=data['guid'], name = None, size = None, tagId=data['fluidalMarkId'], \
                pos=tuple(data["pos"]), rotation=tuple(data["rot"]), isPositional=True)
        else:
            objectData = ObjectData(guid=data['guid'], name=data['name'], tagId=data['fluidalMarkId'], \
                    pos=tuple(data["pos"]), rotation=tuple(data["rot"]), \
                    size=(data["width"], data["height"], data["depth"]), isPositional=False)
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
