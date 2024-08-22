import numpy as np
import cv2
from utils import CameraInfo

def calculateAnglesPos(objectPos,
                       objectSize,
                       objectRot,
                       camInfo: CameraInfo):
    w, h, d = 0.1, 0.1, 0.1#objectSize / 5
    angles = np.zeros((8,3,1))
    angles[0] = np.asarray([- w/2, - h/2, - d/2]).reshape((3, 1))
    angles[1] = np.asarray([- w/2, + h/2, - d/2]).reshape((3, 1))
    angles[2] = np.asarray([+ w/2, + h/2, - d/2]).reshape((3, 1))
    angles[3] = np.asarray([+ w/2, - h/2, - d/2]).reshape((3, 1))

    angles[4] = np.asarray([- w/2, - h/2, + d/2]).reshape((3, 1))
    angles[5] = np.asarray([- w/2, + h/2, + d/2]).reshape((3, 1))
    angles[6] = np.asarray([+ w/2, + h/2, + d/2]).reshape((3, 1))
    angles[7] = np.asarray([+ w/2, - h/2, + d/2]).reshape((3, 1))

    angles, _ = cv2.projectPoints(angles, objectRot, objectPos, camInfo.matrix, camInfo.distCoeffs)

    points = []
    for i in range(8):
        angle = angles[i].reshape(2)
        p1, p2 = angle
        points.append((int(p1), int(p2)))

    return points

def drawBoundingBoxOnFrame(frame,
                           angles,
                           color = (255, 0, 0),
                           thickness = 5):
    for i in range(2):
        color2 = color
        if i == 1:
            color2 = (0, 255, 0)
        for j in range(4):
            p1 = angles[i*4 + j]  
            p2 = angles[i*4 + (j + 1) % 4]
            cv2.line(frame, p1, p2, color2, thickness)

    color3 = (0, 0, 255)
    for i in range(4):
        p1 = angles[i]
        p2 = angles[i+4]
        cv2.line(frame, p1, p2, color3, thickness)

def drawNameAboveMarker(frame,
                        name,
                        markTvec,
                        camInfo: CameraInfo,
                        font = cv2.FONT_HERSHEY_COMPLEX,
                        fontSize = 1,
                        color = (255, 0, 0),
                        thickness = 5,
                        nameShift = 500):
    point,  _ = cv2.projectPoints(markTvec, camInfo.rvec, camInfo.tvec, camInfo.matrix, camInfo.distCoeffs)
    x, y = map((lambda x: max(0, int(x))), point.reshape(2))
    
    cv2.putText(frame, name, (x, y), font, fontSize, color, thickness)

def drawMarkFrame(frame, corners):
    corners = corners.astype(np.int32)
    for i in range(len(corners)):
        cv2.line(frame, corners[i], corners[(i+1)%len(corners)], (0, 0, 255), 2)
    
