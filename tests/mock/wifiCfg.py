class DeviceConfig:
    @classmethod
    def get_wifi(cls):
        return ("SSID", "PASSWORD")

deviceCfg = DeviceConfig

def is_connected():
    return False

def connect(ssid, password, timeout=10, block=False):
    pass

