import zmq
import json
from DataBaseAdapter import MariaDBAdapter
from Server import Server

DEFAULT_SERVER_DATA_PATH = "./Config.json"

def main():
    configPath = input(f"Input path to config file({DEFAULT_SERVER_DATA_PATH} by default): ")
    if configPath == "":
        configPath = DEFAULT_SERVER_DATA_PATH

    with open(configPath, "r") as file:
        config = json.load(file)

    dbAdapter = MariaDBAdapter("./Server/MariaDBConfig.json")
    context = zmq.Context(1)
    server2CameraSocket = config["Server2Camera"]
    server2RevitSocket = config["Server2Revit"][0]
    revit2ServerSocket = config["Revit2Server"][1]
    server = Server(context, server2CameraSocket, revit2ServerSocket, server2RevitSocket, dbAdapter)

    server.startProccessing()

if __name__ == "__main__":
    main()
