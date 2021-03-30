import machine
from config import relay_pin, led_pin

class Switch:
    def __init__(self):
        self.relay = machine.Pin(relay_pin, machine.Pin.OUT)
        self.led = machine.Pin(led_pin, machine.Pin.OUT)
    
    def update_state(self, state):
        # For some reason led 'on()' is off, and 'off()' is on
        print("Updating state")
        if state == 0:
            print("Turning off")
            self.relay.off()
            self.led.on()
        elif state == 1:
            print("Turning on")
            self.relay.on()
            self.led.off()
        return