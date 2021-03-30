import machine
import ustruct
import utime as time
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
    """
    MicroPython Aosong AM2320 I2C driver
    https://github.com/mcauser/micropython-am2320
    MIT License
    Copyright (c) 2016 Mike Causer
    """

    def __init__(self, i2c=None, address=0x5c):
        self.set_client_state = None
        self.i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.address = address
        self.buf = bytearray(8)
    
    def update_state(self, state):
        self.measure()
        temp = self.temperature()
        humd = self.humidity()

        state = {
            "temperature": temp,
            "humdidity": humd
        }
        print(state)
        if self.set_client_state is not None:
            self.set_client_state(state)
        return

    def measure(self):
        buf = self.buf
        address = self.address
        # wake sensor
        try:
            self.i2c.writeto(address, b'')
        except OSError:
            print("OSError!")
            pass
        # read 4 registers starting at offset 0x00
        self.i2c.writeto(address, b'\x03\x00\x04')
        # wait at least 1.5ms
        time.sleep_ms(5)
        # read data
        self.i2c.readfrom_mem_into(address, 0, buf)
        crc = ustruct.unpack('<H', bytearray(buf[-2:]))[0]
        if (crc != self.crc16(buf[:-2])):
            raise Exception("checksum error")
    def crc16(self, buf):
        crc = 0xFFFF
        for c in buf:
            crc ^= c
            for i in range(8):
                if crc & 0x01:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc
    def humidity(self):
        return (self.buf[2] << 8 | self.buf[3]) * 0.1
    def temperature(self):
        t = ((self.buf[4] & 0x7f) << 8 | self.buf[5]) * 0.1
        if self.buf[4] & 0x80:
            t = -t
        return t

    