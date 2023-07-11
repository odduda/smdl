import network
import machine
from time import sleep_ms
from utils import Requests


class DataLogger:
    def __init__(self, settings):
        self.settings = settings
        self.rq = Requests()
        self.wifi = WifiManager(settings["wifi"])
        self.aht = settings["aht"](settings["i2c"])
        self.ads = {}
        self.interval = 5 * 60  # Default is set to 5 minutes
        self.wifi.connect()
        self.server_id = self._get_id()
        self._on_boot()

    def __str__(self):
        return "Data Logger"

    def send(self, path, data):
        return self.rq.post(
            self.settings["host"] + path, data, port=self.settings["port"]
        )

    def get(self, path):
        return self.rq.get(self.settings["host"] + path, port=self.settings["port"])

    def _on_boot(self):
        data = []
        for address, channels in self.settings["devices"].items():
            self.ads[address] = self.settings["ads"](self.settings["i2c"], address, 1)
            for channel in channels:
                data.append(f"{hex(address)}:{channel}")
        self.send(f"/api/server/{self.settings['id']}/onboot", data)

    def _read_aht(self):
        data = {"temperature": self.aht.temperature, "humidity": self.aht.humidity}
        return self.send(f"/api/server/{self.settings['id']}/aht", data)

    def _read_ads(self):
        data = {}
        for address, channels in self.settings["devices"].items():
            for channel in channels:
                for i in range(5):
                    self.ads[address].set_conv(7, channel)
                    sleep_ms(40)
                    data[f"{hex(address)}:{channel}"] = self.ads[address].read_rev()
        return self.send(f"/api/server/{self.settings['id']}/csms", data)

    def read(self):
        self.wifi.connect()
        response_ads = self._read_ads()
        response_aht = self._read_aht()
        if response_ads.status in [400, 500] or response_aht.status in [400, 500]:
            self.interval = 5 * 60
            return self.interval
        data = response_ads.json()
        self.interval = 10 if data["calibrate"] else int(data["interval"]) * 60
        if self.settings["wifi_turn_off"] and not data["calibrate"]:
            self.wifi.disconnect()
        return self.interval


wifi = network.WLAN(network.STA_IF)


class WifiManager:
    def __init__(self, settings):
        self.ssid, self.password = settings
        self.timeout = 60 * 1000

    def _connect(self):
        print("Connecting to wifi")
        count = 0
        wifi.active(True)
        wifi.connect(self.ssid, self.password)
        while not wifi.isconnected():
            if count >= self.timeout:
                print("Failed to connect to wifi, restarting pico")
                machine.reset()
            count += 2
            sleep_ms(2)
        print("Connected! Network config:", wifi.ifconfig())

    def connect(self):
        if not wifi.isconnected():
            self._connect()

    def disconnect(self):
        print("Wifi disconnected!")
        wifi.disconnect()
        wifi.active(False)
