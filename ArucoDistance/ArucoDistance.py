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


def processFrame(frame, camInfo: CameraInfo, markerSize, recognitionProcessor, waitDelay = 1):
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
                    rot, _ = cv2.Rodrigues(np.asarray(response["rot"]).reshape((3, 1)))
                    rot = rvecs[i]

                    DF.drawMarkFrame(frame, corners[i])
                    rot = np.asarray([1 if i == j else 0 for i in range(3) for j in range(3)], dtype=np.float64).reshape((3, 3))
                    angles = DF.calculateAnglesPos(pos, size, rot, camInfo)
                    DF.drawBoundingBoxOnFrame(frame, angles)
                    DF.drawNameAboveMarker(frame, name, tvecs[i], camInfo)

            cv2.drawFrameAxes(frame, camInfo.matrix, camInfo.distCoeffs, rvecs[i], tvecs[i], markerSize * 0.5)
    frame = cv2.resize(frame, (1000, 500))
    cv2.imshow('Frame', frame)
    cv2.waitKey(waitDelay)


def startRecognize(cameraConfig, source, recognitionProcessor, precalibrateMarkerSizeData = None):
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
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        processFrame(frame, cameraInfo,markerSize, recognitionProcessor)

    cap.release()
    cv2.destroyAllWindows()
