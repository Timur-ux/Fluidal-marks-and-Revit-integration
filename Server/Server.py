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
    def __init__(self, context, server2CameraSocket, revit2ServerSocket, server2RevitSocket, dbAdapter: IDataBaseAdapter):
        self.context = context

        self.server2CameraSocket = context.socket(zmq.REP)
        self.server2CameraSocket.connect(server2CameraSocket)
        
        self.revit2ServerSocket = context.socket(zmq.PULL)
        self.revit2ServerSocket.connect(revit2ServerSocket)

        self.poller = zmq.Poller()
        self.poller.register(self.server2CameraSocket, zmq.POLLIN)
        self.poller.register(self.revit2ServerSocket, zmq.POLLIN)
        
        self.server2RevitSocket = context.socket(zmq.PUSH)
        self.server2RevitSocket.connect(server2RevitSocket)

        self.dbAdapter = dbAdapter

        self.camerasPositionData = {}

    def processDetectedMark(self, data):
        tagId, tvec, rvec, cameraId = data["id"], np.asarray(data["tvec"]), np.asarray(data["rvec"]), data["cameraId"]
        if cameraId not in self.camerasPositionData:
            self.camerasPositionData[cameraId] = np.array([0.0, 0.0, 0.0])

        objectData = self.dbAdapter.getData(tagId)
        if objectData is None:
            print(f"Mark not placed in DB detected. Tag id: {tagId}. Skipping...")
            return
        
        if objectData.isPositional:
            cameraRot, _ = cv2.Rodrigues(rvec)
            self.camerasPositionData[cameraId] = np.dot(cameraRot, np.asarray(objectData.markPos) - np.asarray(tvec))
            print(f"Position of camera with id: {cameraId} has updated")
            return

        oldPos = objectData.markPos
        if isObjectMoved(oldPos, tvec):
            objectData.markPos = self.camerasPositionData[cameraId] + tvec
            # self.dbAdapter.updateData(objectData)
            # notifyRevitAboutMovedObject(objectData.guid, tvec, rvec, self.revitSocket) ## Rewrite
            
        cameraRotMatrix, _ = cv2.Rodrigues(self.camerasPositionData[cameraId])
        markRotMatrix, _ = cv2.Rodrigues(rvec)
        markObjVector = objectData.objectPos - objectData.markPos
        objectPos = tvec + markObjVector

        recv = {
                "type" : "DrawObjectBox",
                "name" : objectData.name,
                "size" : list(objectData.size if objectData.size is not None else [0, 0, 0]),
                "pos" : list(objectPos.reshape(3)),
                "rot" : list(rvec.reshape(3))
                }
            
            
        return recv

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
        recv = None
        if data["type"] == "DetectedMark":
            recv = self.processDetectedMark(data)
        elif data["type"] == "PostElementData":
            self.processPostElementData(data);

        return recv

        
    
    def startProccessing(self):
        print("Message proccessing started")
        while True:
            sockets = dict(self.poller.poll())

            if self.revit2ServerSocket in sockets:
                self.process(self.revit2ServerSocket.recv_string())
            if self.server2CameraSocket in sockets:
                recv = self.process(self.server2CameraSocket.recv_string())
                recv = {} if recv is None else recv
                self.server2CameraSocket.send_string(json.dumps(recv))

