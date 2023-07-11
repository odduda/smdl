from machine import Pin, I2C
from ads1x15 import ADS1115
from aht import AHT2x
from time import sleep
from dlpw import DataLogger

settings = {
    "id": 1,
    "i2c": I2C(0, scl=Pin(21), sda=Pin(20)),
    "host": "http://server.local",
    "port": 5000,
    "ads": ADS1115,
    "aht": AHT2x,
    "wifi": ["Pamidore G", "maloPrase25"],
    "wifi_turn_off": True,
    "devices": {
        0x48: [0, 1, 2],
        0x49: [0, 1, 2]
    }
}

server = DataLogger(settings=settings)

while True:
   interval = server.read()
   sleep(interval)
