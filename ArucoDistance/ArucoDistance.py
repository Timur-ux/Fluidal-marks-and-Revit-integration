import numpy as np
import cv2
from pupil_apriltags import Detector
import time
from CameraCalibrator import calibrateMarkerSize

import DrawFunctions as DF
from utils import CameraInfo


MARKER_SIZE = 0.06979
at_detector = Detector(
    families="tagStandard41h12",
    nthreads=4,
    quad_decimate=1.0,
    quad_sigma=0.0,
    refine_edges=1,
    decode_sharpening=0.25,
    debug=0
)

class RotateBuffer:
    def __init__(self, size):
        assert size > 0
        self.size = size
        self.buffer = {}

    def update(self, tagId, newRot):
        if tagId not in self.buffer:
            self.buffer[tagId] = []

        assert len(self.buffer[tagId]) <= self.size

        if len(self.buffer[tagId]) == self.size:
            self.buffer[tagId] = self.buffer[tagId][1:]

        self.buffer[tagId].append(newRot)
    
    def getMean(self, tagId):
        if tagId not in self.buffer:
            return np.ones((3, 3))
        result = self.buffer[tagId][0]
        for rot in self.buffer[tagId][1:]:
            result += rot

        result /= len(self.buffer[tagId])
        return result

def findMarksOnFrame(frame, cameraFCParams, markerSize):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        detectionResult = at_detector.detect(
            gray, estimate_tag_pose=True, camera_params=cameraFCParams, tag_size=markerSize)

        ids = []
        corners = []
        rvecs = []
        tvecs = []
        for result in detectionResult:
            ids.append(result.tag_id)
            corners.append(result.corners)
            rvecs.append(result.pose_R)
            tvecs.append(result.pose_t)

        return ids, corners, tvecs, rvecs


def processFrame(frame, camInfo: CameraInfo, markerSize, recognitionProcessor, waitDelay = 1, resizedFrameShape = None, rotateBuffer: RotateBuffer = RotateBuffer(5)):

    ids, corners, tvecs, rvecs = findMarksOnFrame(frame, camInfo.fcParams, markerSize)
    if ids != []:
        for i in range(len(ids)):
            # Calculate distance
            distance = np.linalg.norm(tvecs[i])
            response = recognitionProcessor.process({ # TODO: send all detected marks by one message
                "distance": distance,
                "tvec" : tvecs[i].T[0],
                "rvec" : list(cv2.Rodrigues(rvecs[i]))[0].T[0],
                "id": ids[i]
            })
            if response is not None and response != {}:
                if response["type"] != "DrawObjectBox":
                    print(f"Undefined response type. Skipping...")
                else:
                    name, size, pos = response["name"], np.asarray(response["size"]), np.asarray(response["pos"]).reshape((3, 1))

                    pos = tvecs[i] 
                    rotateBuffer.update(ids[i], rvecs[i])
                    rot = rotateBuffer.getMean(ids[i])

                    angles = DF.calculateAnglesPos(pos, size, rot, camInfo)
                    DF.drawBoundingBoxOnFrame(frame, angles)
                    DF.drawNameAboveMarker(frame, name, tvecs[i], rot, camInfo)

            cv2.drawFrameAxes(frame, camInfo.matrix, camInfo.distCoeffs, rvecs[i], tvecs[i], markerSize * 0.5)
    if resizedFrameShape is not None:
        frame = cv2.resize(frame, resizedFrameShape)
    cv2.imshow('Frame', frame)
    cv2.waitKey(waitDelay)


def startRecognize(cameraConfig, source, recognitionProcessor, precalibrateMarkerSizeData = None, rotateBufferSize = 50):
    """
        source is a camera id or file's name is containing video
        source may be also image file
        if precalibrateMarkerSizeData as (img with marker, dist to marker, real marker size) is given, marker size will be precalibrated
    """
    cameraMatrix, distCoeffs, tvec, rvec = cameraConfig["cameraMatrix"], cameraConfig["distCoeffs"], cameraConfig["tvec"], cameraConfig["rvec"]
    cameraFCParams = np.asarray([cameraConfig["fx"], cameraConfig["fy"],
                        cameraConfig["cx"], cameraConfig["cy"]])
    cameraInfo = CameraInfo(cameraMatrix, distCoeffs, tvec, rvec, cameraFCParams)

    markerSize = MARKER_SIZE
    if precalibrateMarkerSizeData is not None:
        img, dist, markerSize = precalibrateMarkerSizeData
        markerSize = calibrateMarkerSize(img, markerSize, dist, at_detector, cameraFCParams)

    if type(source) is str and source.endswith(".jpg"):
        processFrame(cv2.imread(source), cameraInfo, markerSize,recognitionProcessor)
        cv2.waitKey(0)
        return

    # Capture video from camera
    cap = cv2.VideoCapture(source)
    rotateBuffer = RotateBuffer(rotateBufferSize)
    resizedFrameShape = (1000, 500)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        processFrame(frame, cameraInfo, markerSize, recognitionProcessor, resizedFrameShape=resizedFrameShape, rotateBuffer=rotateBuffer)
            

    cap.release()
    cv2.destroyAllWindows()
