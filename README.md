# SlothIOT
Repository holding the files for the ESP8266 clients that will be synced using OTA updates

```bash
sudo esptool.py --port /dev/ttyUSB0 erase_flash

sudo esptool.py -p /dev/ttyUSB0 --baud 115200 write_flash --flash_mode=dout --flash_size=detect 0 firmware.bin

cd Client


sudo ampy --port /dev/ttyUSB0 put config.py
sudo ampy --port /dev/ttyUSB0 put senko.py
sudo ampy --port /dev/ttyUSB0 put boot.py
sudo ampy --port /dev/ttyUSB0 put main.py
sudo ampy --port /dev/ttyUSB0 put devices.py
sudo ampy --port /dev/ttyUSB0 put client.py

sudo screen /dev/ttyUSB0 115200
```