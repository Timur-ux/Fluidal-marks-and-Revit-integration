import zmq
import json
import argparse

def main():
    DEFAULT_CONFIG_PATH = "./Config.json"
    parser = argparse.ArgumentParser(
        description="Default argument parser for application control")
    parser.add_argument("--config_path", type=str, default=DEFAULT_CONFIG_PATH,
                        help="path to file with config(json required)")

    namespace = parser.parse_args()

    configPath = namespace.config_path

    config = None
    with open(configPath, "r") as file:
        config = json.load(file)

    if config is None:
        print("Error: can't read config file")
        exit(1)

    currentId = 1
    context = zmq.Context(1)
    serviceSocket = config["InitialDataGiverSocket"]
    socket = context.socket(zmq.REP)
    socket.bind(serviceSocket)

    while True:
        message = socket.recv_string()
        data = {"Id": currentId,
                "Camera2ServerSocket" : config["Camera2Server"]}
        socket.send_string(json.dumps(data))
        currentId += 1
        
if __name__ == "__main__":
    main()
