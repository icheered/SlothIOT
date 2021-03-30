import utime as time
time.sleep(3)
import network
import asyncio 
import machine
from collections import namedtuple
import uwebsockets.client
import urequests as requests
import ujson as json
from config import wifi_ssid, wifi_pass, client_type, client_id, client_pass, server_address, auth_port, auth_path, pubsub_port, pubsub_path
from devices import Switch

# # Wifi SSID and Password
# wifi_ssid = 'HeetPlekje 2.4'
# wifi_pass = 'HeelGeheimWachtwoord'

# # Device Parameters: CHANGE THESE FOR EACH DEVICE AND REGISTER THE DEVICE IN ORCA (SECURITY)
# client_id = "d54abd10-8083-4cc4-b2d5-4d97d6def582"
# device_pass = "$2b$12$0cWzyyUWHqBgz1dBiHedjO7RZ7hbv6MP6OBAwtNSP.0qYCJXEm0gC"

# # IP address or web address of the server
# server_address = "192.168.5.169"

# # Auth API parameters
# auth_port = "4111"
# auth_path = "/api/auth/auth/"

# # PubSub WS parameters
# pubsub_port = "4112"
# pubsub_path = "/ws/pubsub/"

##################################################

pubsub_address = "ws://"+server_address+":"+pubsub_port+pubsub_path
auth_address = "http://"+server_address+":"+auth_port+auth_path

##################################################

print("Config")
print("Client type: "+ client_type)
print("Client ID: "+ client_id)
print("Client pass: "+ client_pass)
print("Wifi SSID: "+ wifi_ssid)
print("Wifi Pass:" + wifi_pass)
print("PubSub Addr: " + pubsub_address)
print("AuthAPI Addr:"+ auth_address)

##################################################

print("Starting")

class Client:
    def __init__(self, loop, wifi_ssid, wifi_pass, pubsub_address, auth_address, client_id, client_pass, device):
        self.loop = loop
        self.wifi_ssid = wifi_ssid
        self.wifi_pass = wifi_pass
        self.pubsub_address = pubsub_address
        self.auth_address = auth_address
        self.client_id = client_id
        self.password = client_pass
        self.hb_interval = 10
        self.token = ""
        self.token_is_valid = False
        self.wifi_connected = False
        self.ws_connected = False
        self.ws = None
        self.state = 0

        self.device = device

        self.initialized = False
        self.sta_if = None

    async def wait_for_wifi(self):
        while not self.wifi_connected:
            await asyncio.sleep(1)
        return
    
    async def wait_for_token(self):
        while self.token == "" or not self.token_is_valid:
            await asyncio.sleep(1)
        return
    
    async def wait_for_ws(self):
        while self.ws is None or not self.ws_connected:
            await asyncio.sleep(1)
        return

    async def connect_wifi(self):
        while True:
            try:
                if not self.wifi_connected:
                    print("Connecting to WIFI")
                    if self.sta_if is None:
                        self.sta_if = network.WLAN(network.STA_IF)
                    while not self.sta_if.isconnected():
                        self.sta_if = network.WLAN(network.STA_IF)
                        self.sta_if.active(True)
                        print("Connecting...")
                        self.sta_if.connect(self.wifi_ssid, self.wifi_pass)
                        await asyncio.sleep(1)
                if not self.wifi_connected and self.sta_if.isconnected():
                    self.wifi_connected = True
                    print("Connected to WIFI")
            except Exception as e:
                print("Error while connecting to WIFI")
                print(e)
            await asyncio.sleep(1)


    async def get_session_token(self):
        while True:
            if not self.token_is_valid:
                try:
                    await self.wait_for_wifi()
                    print("Getting session token")
                    ret = requests.get(self.auth_address+"?client_id="+self.client_id+"&password="+self.password)
                    await asyncio.sleep(1)
                    response = ret.json()
                    if response["type"] == "response":
                        if response["payload"]["status"] == "success":
                            self.token = response["payload"]["token"]
                            print("Token: "+self.token)
                            self.token_is_valid = True
                except Exception as e:
                    print("Error getting session token")
                    print(e)
            await asyncio.sleep(1)
    

    async def connect_ws(self):
        while True:
            if not self.ws_connected:
                self.initialized = False
                try:
                    await self.wait_for_wifi()
                    await self.wait_for_token()
                    print("Connecting to server WS")

                    ws = await uwebsockets.client.connect(self.pubsub_address, self.token)
                    #ws = await conn._connect(self.token)
                    self.ws = ws
                    self.ws_connected = True
                    print("Connected")
                    await self.init_topics()
                except Exception as e:
                    print("Error conencting to WS")
                    print(e)
            await asyncio.sleep(1)
    

    async def handle_message(self):
        while True:
            await self.wait_for_wifi()
            await self.wait_for_token()
            await self.wait_for_ws()
            try: 
                data = None
                try:
                    data = await self.ws.recv()
                except Exception as e:
                    print("Something went wrong while retrieving data")
                    print(e)
                    if "ECONNABORTED" in str(e):
                        print("WIFI connection lost")
                        self.ws_connected = False
                        self.wifi_connected = False
                if data is not None:
                    print("Message")
                    print(data)
                    s = data.replace("'", '"')
                    msg = json.loads(s)
                    if "type" in msg:
                        if msg["type"] == "init":
                            self.hb_interval = int(msg["payload"]["heartbeat_interval"])
                            print("Received sysinfo " + str(self.hb_interval))
                        elif msg["type"] == "response":
                            # Should I handle this? Idk
                            if "status" in msg["payload"]:
                                pass
                        elif msg["type"] == "topic":
                            if "command" in msg["payload"] and msg["payload"]["command"] == "get":
                                await self.send_state()
                            elif "command" in msg["payload"] and msg["payload"]["command"] == "set":
                                if "data" in msg["payload"]:
                                    value = float(msg["payload"]["data"])
                                    self.state = value
                                    await self.update_state()
                                else:
                                    print("Should set state but didn't get state")
            except Exception as e:
                print("Error while handling message")
                print(e)
                if "syntax error in JSON" in str(e):
                    self.ws_connected = False
                await asyncio.sleep(3)
            #await asyncio.sleep(1)


    async def send_state(self):
        print("Sending state")
        clid = "eec2d72c9a7f42ddab19e1ae5cad5150"
        message = {
            "type": "topic",
            "payload": {
                "action": "pub",
                "name": "state",
                "data": self.state,
                "client_id": ""
            }
        }
        await self.send_message(message)

    async def update_state(self):
        print("Updating state")
        self.device.update_state(self.state)
        await self.send_state()


    async def send_heartbeat(self):
        msg = {
            "type": "heartbeat"
        }
        while True:
            await self.wait_for_wifi()
            await self.wait_for_token()
            await self.wait_for_ws()

            await asyncio.sleep(self.hb_interval)
            print("Sending heartbeat")
            await self.send_message(msg)


    async def send_message(self, message):
        await self.wait_for_wifi()
        await self.wait_for_token()
        await self.wait_for_ws()
        print("Sending...")
        print(message)
        msg = str(message)
        try:
            await self.ws.send(msg)
        except Exception as e:
            print("Sending failed: "+str(e))
            if "ECONNRESET" in str(e):
                print("WS connection lost")
                self.ws_connected = False
            if "ECONNABORTED" in str(e):
                print("WIFI connection lost")
                self.ws_connected = False
                self.wifi_connected = False
        return


    async def init_topics(self):
        await self.wait_for_wifi()
        await self.wait_for_token()
        await self.wait_for_ws()

        if not self.initialized:
            print("Initializing topics")
            self.initialized = True
            # Create a comm and a sub topic for this device
            msg = {
                "type": "topic",
                "payload": {
                    "action": "create",
                    "type": "basic"
                }
            }
            await self.send_message(msg)
            # Subscribe to this client's comm topic
            sub_comm_topic = {
                "type": "topic",
                "payload": {
                    "action": "sub",
                    "client_id": self.client_id,
                    "name": "comm"
                }
            }
            await self.send_message(sub_comm_topic)

            # Request initial parameters
            init = {
                "type": "init"
            }
            await self.send_message(init)
        return


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