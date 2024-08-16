import numpy as np
import cv2
from pupil_apriltags import Detector
import time
from CameraCalibrator import calibrateMarkerSize


marker_size = 0.0724
def processImage(img, at_detector, camera_matrix, dist_coeffs, camera_fc_params):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cellSize = (int(img.shape[1]/10), int(img.shape[0]/10))
    
    detectionResult = at_detector.detect(
        gray, estimate_tag_pose=True, camera_params=camera_fc_params, tag_size=marker_size)

    ids = []
    corners = []
    rvecs = []
    tvecs = []
    for result in detectionResult:
        ids.append(result.tag_id)
        corners.append(result.corners)
        rvecs.append(result.pose_R)
        tvecs.append(result.pose_t)

    if ids != []:
        for i in range(len(ids)):
            # Calculate distance
            distance = np.linalg.norm(tvecs[i])

            cv2.drawFrameAxes(img, camera_matrix, dist_coeffs,
                              rvecs[i], tvecs[i], marker_size * 0.5)
            cv2.putText(img, f"Dist: {distance:.5f}m z: {tvecs[i][2][0]:.5f}", (int(cellSize[0]*1.5), cellSize[1]), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 5, cv2.LINE_AA)
            cv2.putText( img, f"Id: {ids[i]}", (cellSize[0]*2, cellSize[1]*2), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 5, cv2.LINE_AA)

    img = cv2.resize(img, (1600, 800))
    cv2.imshow('Frame', img)
    cv2.waitKey(0)


def startRecognize(camera_config, source, recognitionProcessor, precalibrateMarkerSizeData = None):
    """
        source is a camera id or file's name is containing video
        source may be also image file
        if precalibrateMarkerSizeData as (img with marker, dist to marker, real marker size) is given, marker size will be precalibrated
    """
    
    camera_matrix = np.asarray(camera_config["cameraMatrix"])
    dist_coeffs = np.asarray(camera_config["distCoeffs"])
    camera_fc_params = np.asarray([camera_config["fx"], camera_config["fy"],
                        camera_config["cx"], camera_config["cy"]])
    at_detector = Detector(
        families="tagStandard41h12",
        nthreads=4,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )
    if precalibrateMarkerSizeData is not None:
        img, dist, markerSize = precalibrateMarkerSizeData
        marker_size = calibrateMarkerSize(img, markerSize, dist, at_detector, camera_fc_params)

    if type(source) is str and source.endswith(".jpg"):
        processImage(cv2.imread(source), at_detector, camera_matrix, dist_coeffs, camera_fc_params)
        return

    # Capture video from camera
    cap = cv2.VideoCapture(source)
    firstFrame = True
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        detectionResult = at_detector.detect(
            gray, estimate_tag_pose=True, camera_params=camera_fc_params, tag_size=marker_size)

        ids = []
        corners = []
        rvecs = []
        tvecs = []
        for result in detectionResult:
            ids.append(result.tag_id)
            corners.append(result.corners)
            rvecs.append(result.pose_R)
            tvecs.append(result.pose_t)

        if ids != []:
            for i in range(len(ids)):
                # Calculate distance
                distance = np.linalg.norm(tvecs[i])

                recognitionProcessor.process({
                    "distance": distance,
                    "tvec" : tvecs[i].T[0],
                    "rvec" : cv2.Rodrigues(rvecs[i]).T[0],
                    "id": ids[i]
                })
                cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs,
                                  rvecs[i], tvecs[i], marker_size * 0.5)
                cv2.putText(frame, f"Dist: {distance:.2f}m x: {tvecs[i][0][0]:.2f} y: {tvecs[i][1][0]:.2f} z: {tvecs[i][2][0]:.2f}", (
                    10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(
                    frame, f"Id: {ids[i]}", (100, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow('Frame', frame)
        if (firstFrame):
            cv2.waitKey(0)
            firstFrame = False
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
