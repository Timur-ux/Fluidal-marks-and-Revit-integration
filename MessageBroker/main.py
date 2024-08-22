import zmq
import json

DEFAULT_CONFIG_PATH = "./Config.json"

def main():
    configPath = input(f"Input config path({DEFAULT_CONFIG_PATH} by default): ")
    if configPath == "":
        configPath = DEFAULT_CONFIG_PATH
    with open(configPath, "r") as file:
        config = json.load(file)

    print(f"Starting broker with:")
    for k,v in config.items():
        print(k, ":", v)

    context = zmq.Context(1)

    revit2ServerSocket = [context.socket(zmq.PULL), context.socket(zmq.PUSH)]
    server2RevitSocket = [context.socket(zmq.PULL), context.socket(zmq.PUSH)]
    camera2ServerSocket = context.socket(zmq.ROUTER)
    server2CameraSocket = context.socket(zmq.DEALER)

    camera2ServerSocket.bind(config["Camera2Server"])
    server2CameraSocket.bind(config["Server2Camera"])

    for i in range(2):
        revit2ServerSocket[i].bind(config["Revit2Server"][i])
        server2RevitSocket[i].bind(config["Server2Revit"][i])
    
    
    poller = zmq.Poller()
    poller.register(camera2ServerSocket, zmq.POLLIN)
    poller.register(server2CameraSocket, zmq.POLLIN)
    for i in range(2):
        poller.register(revit2ServerSocket[i], zmq.POLLIN)
        poller.register(server2RevitSocket[i], zmq.POLLIN)

    while True:
        try:
            sockets = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if camera2ServerSocket in sockets:
            message = camera2ServerSocket.recv_multipart()
            print("Camera to Server:", message)
            server2CameraSocket.send_multipart(message)

        if server2CameraSocket in sockets:
            message = server2CameraSocket.recv_multipart()
            print("Server to camera:", message)
            camera2ServerSocket.send_multipart(message)

        if revit2ServerSocket[0] in sockets:
            message = revit2ServerSocket[0].recv_multipart()
            print("Revit to Server:", message)
            revit2ServerSocket[1].send_multipart(message)

        if server2RevitSocket[0] in sockets:
            message = server2RevitSocket[0].recv_multipart()
            print("Server to Revit:", message)
            server2RevitSocket[1].send_multipart(message)




if __name__ == "__main__":
    main()
