# Soil Moisture Data Logger

Measuring soil moisture, air temperature and humidity using Raspberry Pico W with micropython, ADS1X15 and AHT2X. 


- Download [Thorny IDE](https://thonny.org/)

- Flash Pico W with micropython

- Upload files from fw directory to pico

## Firmware

```py
# main.py example
from smdl import DataLogger
from ads1x15 import ADS1115
from aht import AHT2x
settings = {
    "id": 1, # Server ID
    "i2c": I2C(0, scl=Pin(21), sda=Pin(20)),
    "host": "http://server.local", # Server host, must include " http:// "
    "port": 5000,
    "ads": ADS1115,
    "aht": AHT2x,
    "wifi": ["Pamidore G", "maloPrase25"], # WIFI ssid and password
    "wifi_turn_off": True, # Turn off wifi after reading sensors
    "devices": { # { I2C Address: [...channels] }
        0x48: [0, 1, 2],
        0x49: [0, 1, 2]
    }
}
server = DataLogger(settings=settings) # Init server

while True:
   interval = server.read() # Read sensors
   sleep(interval) # 

```

## HTTP Client

### Requirements

- Flask
- requests

Navigate to the empty directory and run the following commands

```bash
git clone https://github.com/odduda/smdl

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

cd http

flask run --host=0.0.0.0 -p 5000
```

If you want to use WSGI server you can follow the steps here -> [Flask docs](https://flask.palletsprojects.com/en/2.2.x/deploying/)

**RUN THE SERVER ONLY IN THE HOME NETWORK!!!**

### Calibrating the ADS

- Activate calibration in the header
- Wait til Pico starts reading values every 10 seconds
- Submerge csms sensor in the water and record the highest value
- Wipe off csms sensor with a clean cloth and record the lowest value
- and click on update.

## Examples

![Alt text](./http/static/img/aht.png?raw=true "Aht Graph")

![Alt text](./http/static/img/server.png?raw=true "Server Dashboard")

![Alt text](./http/static/img/index.png?raw=true "Index Page")