#Imports
import time
import json
import traceback
import docker
import subprocess
import os
import tempfile
import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    IoTCoreMessage,
    QOS,
    SubscribeToIoTCoreRequest
)

TIMEOUT = 10
ipc_client = awsiot.greengrasscoreipc.connect()

topic = "docker"
qos = QOS.AT_MOST_ONCE

#IPC Stream Handler
class StreamHandler(client.SubscribeToIoTCoreStreamHandler):
    def __init__(self):
        super().__init__()

    def on_stream_event(self, event: IoTCoreMessage) -> None:
        message = json.loads(event.message.payload.decode())

        try:
            client = docker.from_env()
            name = message["name"]
            command = message["command"]
        
            if command == "start":
                container = client.containers.get(name)
                container.start()
                print("Starting container: " + name)
        
            elif command == "pause":
                container = client.containers.get(name)
                result = json.loads(container.pause())
                print(result)
                print("Pausing container: " + name)
                
            elif command == "unpause":
                container = client.containers.get(name)
                print(container.unpause())
                print("Unpausing container: " + name)
                
            elif command == "stop":
                container = client.containers.get(name)
                container.stop()
                print("Stopping container: " + name)
                
            else:
                print("Error")
            
        except:
            with tempfile.TemporaryFile() as tmp:
                tmp.write("Docker Error")
                
    def on_stream_error(self, error: Exception) -> bool:
        message_string = "Error!"

        return True

    def on_stream_closed(self) -> None:
        pass
        
#Initiate Subscription
request = SubscribeToIoTCoreRequest()
request.topic_name = topic
request.qos = qos
handler = StreamHandler()
operation = ipc_client.new_subscribe_to_iot_core(handler)
future = operation.activate(request)
future_response = operation.get_response()
future_response.result(TIMEOUT)

while True:
    time.sleep(1)

operation.close()
