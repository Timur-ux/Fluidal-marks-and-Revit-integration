import CameraCalibrator as CC
import ArucoDistance as AD
import argparse
import json
import utils
import zmq
import numpy as np
import time

DEFAULT_CALIBRATION_RESULT_PATH = "./CalibrationResult.json"
DEFAULT_SERVER_DATA_PATH = "./Config.json"


class RecognitionProcessor:
    def __init__(self, context: zmq.Context, sockAddr):
        self.context = context
        self.socket = context.socket(zmq.PUSH)
        self.socket.connect(sockAddr)

    def process(self, data):
        data["type"] = "DetectedMark";
        print("Sending data:", data)
        self.socket.send_string(json.dumps(data, cls=utils.NumpyToJsonEncoder))

class DummyRecognitionProcessor:
    """if data processing is not needed use dummy processor"""
    def process(self, data):
        pass

def calibrate(camera_index):
    calibrationFilePath = input(
        f"Input path calibration results will be stored({DEFAULT_CALIBRATION_RESULT_PATH} by default): ")
    if calibrationFilePath == "":
        calibrationFilePath = DEFAULT_CALIBRATION_RESULT_PATH

    camera_config = CC.calibrateUsingCamera(
        camera_index, doLog=True)
    utils.dumpConfig(calibrationFilePath, camera_config)

    print(f"Calibration result: \n {camera_config}")
    print(f"It is stored at: {calibrationFilePath}")


def startRecognition(camera_index):
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
    cameraSocket = netConfig["ClientSocket"]
    recognitionProcessor = DummyRecognitionProcessor()#RecognitionProcessor(context, cameraSocket)

    now = time.time()
    AD.startRecognize(camera_config, camera_index,
                      recognitionProcessor)
    print(f"time: {time.time() - now}")


def main():
    parser = argparse.ArgumentParser(
        description="Default argument parser for application control")
    parser.add_argument("--calibrate", type=bool, default=False,
                        help="point if camera is need to calibrate(Default: False)")
    parser.add_argument("--camera_index", type=int, default=0,
                        help="point camera index that will be calibrated(Default: 0)")
    parser.add_argument("--source_path", type=str, default="",
                        help="point source (video/image) to aruco estimate(Default: "")")

    namespace = parser.parse_args()

    camera_index = namespace.camera_index
    source_path = namespace.source_path
    if namespace.calibrate:
        calibrate(camera_index)
    elif source_path != "":
        startRecognition(source_path)
    else:
        startRecognition(camera_index)



if __name__ == "__main__":
    main()
