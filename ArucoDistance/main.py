import CameraCalibrator as CC
import ArucoDistance as AD
import argparse
import json
import utils
import zmq
import numpy as np
import time
import cv2

DEFAULT_CALIBRATION_RESULT_PATH = "./CalibrationResult.json"
DEFAULT_SERVER_DATA_PATH = "./Config.json"


class RecognitionProcessor:
    def __init__(self, context: zmq.Context, sockAddr, cameraId):
        self.context = context
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(sockAddr)
        self.cameraId = cameraId

    def process(self, data):
        data["type"] = "DetectedMark";
        data["cameraId"] = self.cameraId
        print("Sending data:", data)
        self.socket.send_string(json.dumps(data, cls=utils.NumpyToJsonEncoder))
        return json.loads(self.socket.recv_string())

class DummyRecognitionProcessor:
    """if data processing is not needed use dummy processor"""
    def process(self, data):
        return None

def calibrate(imagesPath, fileName):
    camera_config = CC.calibrateUsingImages(imagesPath)
    utils.dumpConfig(fileName, camera_config)

    print(f"Calibration result: \n {camera_config}")
    print(f"It is stored at: {fileName}")


def startRecognition(camera_index, precalibrateMarkerSizeData = None, remoteCameraId=None):
    calibrationFilePath = input(
        f"Input path to camera's calibration file({DEFAULT_CALIBRATION_RESULT_PATH} by default): ")
    if calibrationFilePath == "":
        calibrationFilePath = DEFAULT_CALIBRATION_RESULT_PATH

    camera_config = utils.loadCameraConfig(calibrationFilePath)
    netConfigPath = input(
        f"Input path to net config where server's or broker's socket stored({DEFAULT_SERVER_DATA_PATH} by default): ")
    if netConfigPath == "":
        netConfigPath = DEFAULT_SERVER_DATA_PATH

    with open(netConfigPath, "r") as file:
        netConfig = json.load(file)

    context = zmq.Context(1)
    initialDataGiverSocket = context.socket(zmq.REQ)
    initialDataGiverSocket.connect(netConfig["InitialDataGiverSocket"]) 
    initialDataGiverSocket.send_string("")

    request = initialDataGiverSocket.recv_string()
    data = json.loads(request)

    clientSocket = data["Camera2ServerSocket"]
    if remoteCameraId is None:
        remoteCameraId = data["Id"]
    recognitionProcessor = RecognitionProcessor(context, clientSocket, remoteCameraId)

    now = time.time()
    AD.startRecognize(camera_config, camera_index,
                      recognitionProcessor, precalibrateMarkerSizeData)
    print(f"time: {time.time() - now}")


def main():
    parser = argparse.ArgumentParser(
        description="Default argument parser for application control")
    parser.add_argument("--calibrate_images", type=str, default="",
                        help="if path to images is given, camera will be calibrated(Default: "")")
    parser.add_argument("--camera_calib_file_name", type=str, default=DEFAULT_CALIBRATION_RESULT_PATH, help="Will be saved as .json file")
    parser.add_argument("--camera_index", type=int, default=0,
                        help="point camera index that will be calibrated(Default: 0)")
    parser.add_argument("--source_path", type=str, default="",
                        help="point source (video/image) to aruco estimate(Default: "")")
    parser.add_argument("--precalibrateMarkerSizeData", type=tuple[str, float, float], default=None, help="if (path to img with marker, dist to marker, real marker size) is given, marker size will be precalibrated ")
    parser.add_argument("--remote_cameraId", type=int, default=0, help="Will use id from InitialDataGiver service if 0")

    namespace = parser.parse_args()

    camera_index = namespace.camera_index
    source_path = namespace.source_path
    precalibrateMarkerSizeData = namespace.precalibrateMarkerSizeData
    if precalibrateMarkerSizeData is not None:
        precalibrateMarkerSizeData = "".join(precalibrateMarkerSizeData[1:-1]).split(',')
        path, dist, markerSize = precalibrateMarkerSizeData
        dist = float(dist)
        markerSize = float(markerSize)
        precalibrateMarkerSizeData = (cv2.imread(path), dist, markerSize)

    if namespace.calibrate_images != "":
        calibrate(namespace.calibrate_images, namespace.camera_calib_file_name)
    elif source_path != "":
        startRecognition(source_path, precalibrateMarkerSizeData, namespace.remote_cameraId)
    else:
        startRecognition(camera_index, precalibrateMarkerSizeData, namespace.remote_cameraId)



if __name__ == "__main__":
    main()
