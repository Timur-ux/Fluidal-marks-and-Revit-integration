import numpy as np
import cv2 as cv
import glob
import time

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

EVALUATION_ERROR = 0.001

def calibrateUsingImages(dirWithImages):
    objp = np.zeros((9*6, 3), np.float32)
    objp[:, :2] = np.mgrid[0:6, 0:9].T.reshape(-1, 2)

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    images = glob.glob(f'{dirWithImages}/*.jpg')
    gray = None
    for fname in images:
        img = cv.imread(fname)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, (6, 9), None)

        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)

            corners2 = cv.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

    if len(objpoints) == 0 or gray is None:
        print("Error in calibrateUsingImages: Bad images, can't calibrate")
        return {}
    mtx_fake = np.zeros((3, 3))
    dist_fake = np.zeros((1, 5))
    ret, mtx, dist, _, _ = cv.calibrateCamera(
        objpoints, imgpoints, gray.shape, mtx_fake, dist_fake, None, None, 0, criteria)
    ret, rvec, tvec = cv.solvePnP(np.array(objpoints[0]),np.array(imgpoints[0]), mtx, dist, None, None, flags=cv.SOLVEPNP_EPNP)

    return {
        "cameraMatrix": mtx,
        "distCoeffs": dist,
        "rvec": rvec,
        "tvec": tvec,
        "fx": mtx[0][0],
        "fy": mtx[1][1],
        "cx": mtx[0][2],
        "cy": mtx[1][2],
    }

def calibrateMarkerSize(imgWithMark, realMarkerSize, realDistanceToMarker, detector, camera_fc_params, eps=EVALUATION_ERROR):
    gray = cv.cvtColor(imgWithMark, cv.COLOR_BGR2GRAY)
    lowerS, higherS = realMarkerSize / 10, realMarkerSize * 10
    midS = (lowerS + higherS)/2
    midD = 1e8
    i = 0
    while abs(realDistanceToMarker - midD) > eps:
        if realDistanceToMarker < midD:
            higherS = midS
        else:
            lowerS = midS
        midS = (lowerS + higherS)/2
        midD = np.linalg.norm(detector.detect(gray, estimate_tag_pose=True, camera_params=camera_fc_params, tag_size=midS)[0].pose_t)
        print(f"Step {i}: midS: {midS}, minD: {midD}")
        i += 1

    return midS


