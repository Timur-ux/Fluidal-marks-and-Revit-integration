import zmq
import json
from DataBaseAdapter import IDataBaseAdapter
from objectData import ObjectData
import numpy as np
import cv2

EVALUATION_ERROR = 0.05

def isObjectMoved(oldPos, curPos):
    '''calc module of distance between 2 object poses and compare it with EVALUATION_ERROR'''
    difference = np.sqrt(np.sum((oldPos - curPos)**2))

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

        self.camerasPositionData = {}

    def processDetectedMark(self, data):
        tagId, tvec, rvec, cameraId = data["id"], np.asarray(data["tvec"]), np.asarray(data["rvec"]), data["cameraId"]

        objectData = self.dbAdapter.getData(tagId)
        if objectData is None:
            print(f"Mark not placed in DB detected. Tag id: {tagId}. Skipping...")
            return
        
        if objectData.isPositional:
            self.camerasPositionData[cameraId] = [np.asarray(tvec) + np.asarray(objectData.markPos), rvec]
            return

        oldPos = objectData.markPos
        if isObjectMoved(oldPos, tvec):
            objectData.markPos = self.camerasPositionData[cameraId][0] + tvec
            
            cameraRotMatrix, _ = cv2.Rodrigues(self.camerasPositionData[cameraId][1])
            markRotMatrix, _ = cv2.Rodrigues(rvec)
            resultRotMatrix = cameraRotMatrix @ markRotMatrix
            resultRot = cv2.Rodrigues(resultRotMatrix)

            objectData.rotation_ = resultRot
            self.dbAdapter.updateData(objectData)
            notifyRevitAboutMovedObject(objectData.guid(), tvec, rvec, self.revitSocket)

    def processPostElementData(self, data):
        guid = data['guid']
        tagId = data['fluidalMarkId']
        markPos = np.asarray(data['markPos'])
        objectPos = np.asarray(data['objectPos'])
        isPositional = data['isPositional']
        if isPositional:
            objectData = ObjectData(
                    guid=guid
                    , tagId=tagId
                    , markPos=markPos
                    , objectPos=objectPos
                    , isPositional=True)
        else:
            name = data['name']
            size = np.asarray(data['size'])
            objectData = ObjectData(
                    guid=guid
                    , name = name
                    , tagId=tagId
                    , markPos=markPos
                    , objectPos=objectPos
                    , isPositional=False
                    , size = size)
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
