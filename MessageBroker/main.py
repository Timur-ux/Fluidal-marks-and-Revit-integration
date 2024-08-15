import zmq
import json

DEFAULT_CONFIG_PATH = "./Config.json"

def main():
    configPath = input(f"Input config path({DEFAULT_CONFIG_PATH} by default): ")
    if configPath == "":
        configPath = DEFAULT_CONFIG_PATH
    with open(configPath, "r") as file:
        config = json.load(file)

    print(f"Starting broker with\n \
          CameraSocket: {config['ClientSocket']}\n \
          ServerSocket: {config['ServerSocket']}\n \
          RevitFrontend: {config['RevitClient']}\n \
          RevitBackend: {config['RevitServer']}")

    context = zmq.Context(1)

    frontend = context.socket(zmq.PULL)
    revitFrontend = context.socket(zmq.PULL)

    revitBackend = context.socket(zmq.PUSH)
    backend = context.socket(zmq.PUSH)

    frontend.bind(config["ClientSocket"])
    backend.bind(config["ServerSocket"])

    revitFrontend.bind(config["RevitClient"])
    revitBackend.bind(config["RevitServer"])
    
    
    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(revitFrontend, zmq.POLLIN)

    while True:
        try:
            sockets = dict(poller.poll())
        except KeyboardInterrupt:
            break

        if frontend in sockets:
            message = frontend.recv_multipart()
            print("Frontend:", message)
            backend.send_multipart(message)
       
        if revitFrontend in sockets:
            message = revitFrontend.recv_multipart()
            print("Revit frontend:", message)
            revitBackend.send_multipart(message)


if __name__ == "__main__":
    main()
