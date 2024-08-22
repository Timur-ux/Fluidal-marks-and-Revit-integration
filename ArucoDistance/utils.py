import json
from json import JSONEncoder
import numpy as np
import yaml


class NumpyToJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


def dumpConfig(path, config):
    with open(path, "w") as file:
        json.dump(config, file, cls=NumpyToJsonEncoder)


def loadCameraConfig(path: str):
    if path.endswith(".json"):
        with open(path, "r") as file:
            camera_config = json.load(file)
        camera_config["cameraMatrix"] = np.asarray(
            camera_config["cameraMatrix"])
        camera_config["distCoeffs"] = np.asarray(camera_config["distCoeffs"])
        camera_config["rvec"] = np.asarray(camera_config["rvec"])
        camera_config["tvec"] = np.asarray(camera_config["tvec"])
        return camera_config
    elif path.endswith(".yaml"):
        with open(path, "r") as file:
            camera_config = yaml.safe_load(file)
        return camera_config

class CameraInfo:
    def __init__(self, matrix, distCoeffs, tvec, rvec, fcParams = None):
        self.matrix = matrix
        self.distCoeffs = distCoeffs
        self.tvec = tvec
        self.rvec = rvec
        if fcParams is None:
            self.fcParams = np.asarray([matrix[0][0], matrix[1][1], matrix[0][2], matrix[1][2]])
        else:
            self.fcParams = fcParams
