import machine
import am2320
from machine import I2C, Pin

from config import relay_pin, led_pin, scl_pin, sda_pin




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

class AM2320:
    def __init__(self):
        self.set_client_state = None
        i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.sensor = am2320.AM2320(self.i2c)
    
    def update_state(self, state):
        self.sensor.measure()
        temp = self.sensor.temperature()
        humd = self.sensor.humidity()

        state = {
            "temperature": temp,
            "humdidity": humd
        }
        print(state)
        if self.set_client_state is not None:
            self.set_client_state(state)
        return