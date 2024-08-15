import zmq
import json
from DataBaseAdapter import IDataBaseAdapter, MariaDBAdapter
from Server import Server, notifyRevitAboutMovedObject
from objectData import ObjectData
import time

DEFAULT_SERVER_DATA_PATH = "./Config.json"

def main():
    configPath = input(f"Input path to config file({DEFAULT_SERVER_DATA_PATH} by default): ")
    if configPath == "":
        configPath = DEFAULT_SERVER_DATA_PATH

    with open(configPath, "r") as file:
        config = json.load(file)

    dbAdapter = MariaDBAdapter("./Server/MariaDBConfig.json")
    context = zmq.Context(1)
    serverSocket = config["ServerSocket"]
    revitSocket = config["RevitClient"]
    server = Server(context, serverSocket, revitSocket, dbAdapter)

    server.startProccessing()

# def TestRevitObjectsMoves():
#     configPath = input(f"Input path to config file({DEFAULT_SERVER_DATA_PATH} by default): ")
#     if configPath == "":
#         configPath = DEFAULT_SERVER_DATA_PATH
#
#     with open(configPath, "r") as file:
#         config = json.load(file)
#
#     dbAdapter = MariaDBAdapter("./Server/MariaDBConfig.json")
#     context = zmq.Context(1)
#     serverSocket = config["ServerSocket"]
#     revitSocket = config["RevitClient"]
#     server = Server(context, serverSocket, revitSocket, dbAdapter)
#
#     testObject = dbAdapter.getData(3211254)
#     newTestObject = ObjectData(guid=testObject.guid(), name=testObject.name(), tagId=testObject.tagId(), pos=testObject.pos(), size=testObject.size())
#     newTestObject.pos_ = [sum(x) for x in zip((4, 0, 0), newTestObject.pos_)]
#     while True:
#         print(testObject.pos(), newTestObject.pos())
#         time.sleep(10)
#         notifyRevitAboutMovedObject(testObject, newTestObject, server.revitSocket)
#         testObject, newTestObject = newTestObject, testObject
#         print(testObject.pos(), newTestObject.pos())

if __name__ == "__main__":
    main()
    # TestRevitObjectsMoves()
