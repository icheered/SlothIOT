import utime as time
time.sleep(3)

print("Starting")
from client import Client

import asyncio 
from config import wifi_ssid, wifi_pass, client_type, client_id, client_pass, server_address, auth_port, auth_path, pubsub_port, pubsub_path
from devices import Switch


pubsub_address = "ws://"+server_address+":"+pubsub_port+pubsub_path
auth_address = "http://"+server_address+":"+auth_port+auth_path


print("Config")
print("Client type: "+ client_type)
print("Client ID: "+ client_id)
print("Client pass: "+ client_pass)
print("Wifi SSID: "+ wifi_ssid)
print("Wifi Pass:" + wifi_pass)
print("PubSub Addr: " + pubsub_address)
print("AuthAPI Addr:"+ auth_address)

##################################################

loop = asyncio.get_event_loop()

device = None
if client_type == "switch":
    device = Switch()

client = Client(loop=loop, 
                wifi_ssid=wifi_ssid,
                wifi_pass=wifi_pass,
                pubsub_address=pubsub_address, 
                auth_address=auth_address, 
                client_id=client_id, 
                client_pass=client_pass,
                device=device)

task = asyncio.Task(client.connect_wifi())
task = asyncio.Task(client.get_session_token())
task = asyncio.Task(client.connect_ws())
task = asyncio.Task(client.send_heartbeat())
task = asyncio.Task(client.handle_message())

loop.run_forever()