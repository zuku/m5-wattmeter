import unittest
from unittest.mock import MagicMock
from mock import ujson, uos, logging
import os, tempfile, json
import wmconfig

class TestWMConfig(unittest.TestCase):
    def getAssetFilePath(self, file_name):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", file_name)

    def getAssetJson(self, file_name):
        file_path = self.getAssetFilePath(file_name)
        with open(file_path, "r") as f:
            return json.load(f)

    def setUp(self):
        uos.ADD_ENTRIES = []

    def test_isFileExists(self):
        uos.ADD_ENTRIES.append(("testfile", 0x8000, 0))
        uos.ADD_ENTRIES.append(("testdir", 0x4000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        self.assertTrue(config._isFileExists("testfile"))
        self.assertFalse(config._isFileExists("testdir"))
        self.assertFalse(config._isFileExists("notexists"))

    def test_isFileExists_abs_path(self):
        uos.ADD_ENTRIES.append(("testfile", 0x8000, 0))
        ilistdir_bak = uos.ilistdir
        try:
            uos.ilistdir = MagicMock(return_value=uos.ENTRIES+uos.ADD_ENTRIES)
            config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
            self.assertTrue(config._isFileExists("/path/to/testfile"))
            uos.ilistdir.assert_called_once_with("/path/to")
        finally:
            uos.ilistdir = ilistdir_bak

    def test_isFileExists_rel_path(self):
        uos.ADD_ENTRIES.append(("testfile", 0x8000, 0))
        ilistdir_bak = uos.ilistdir
        try:
            uos.ilistdir = MagicMock(return_value=uos.ENTRIES+uos.ADD_ENTRIES)
            config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
            self.assertTrue(config._isFileExists("path/to/testfile"))
            uos.ilistdir.assert_called_once_with("path/to")
        finally:
            uos.ilistdir = ilistdir_bak

    def test_deepCopy(self):
        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        src = {
            "a": "A",
            "b": [1, 2, 3],
            "c": {
                "d": "D",
                "e": [4, {"0": "1"}, 6],
                "f": {
                    "g": "G",
                    "h": {}
                }
            }
        }
        dst0 = src
        dst0["a"] = "Y"
        self.assertEqual(dst0, src)

        dst1 = config._deepCopy(src)
        self.assertEqual(dst1, src)
        self.assertNotEqual(id(dst1["b"]), id(src["b"]))
        self.assertNotEqual(id(dst1["c"]), id(src["c"]))
        self.assertNotEqual(id(dst1["c"]["e"]), id(src["c"]["e"]))
        self.assertNotEqual(id(dst1["c"]["e"][1]), id(src["c"]["e"][1]))
        self.assertNotEqual(id(dst1["c"]["f"]), id(src["c"]["f"]))
        self.assertNotEqual(id(dst1["c"]["f"]["h"]), id(src["c"]["f"]["h"]))

        dst2 = config._deepCopy(src)
        dst2["a"] = "X"
        self.assertNotEqual(dst2, src)

        dst3 = config._deepCopy(src)
        dst3["b"][1] = 0
        self.assertNotEqual(dst3, src)

    def test_recursiveMerge(self):
        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        base = {
            "a": "A",
            "b": [1, 2, 3],
            "c": {
                "d": "D",
                "e": [4, {"0": "1"}, 6],
                "f": {
                    "g": "G",
                    "h": {}
                },
                "n": None,
                "t": True
            }
        }
        overwrite = {
            "c": {
                "e": [1, 2, 3]
            },
            "i": "J"
        }
        actual = config._recursiveMerge(base, overwrite)
        expected = {
            "a": "A",
            "b": [1, 2, 3],
            "c": {
                "d": "D",
                "e": [1, 2, 3],
                "f": {
                    "g": "G",
                    "h": {}
                },
                "n": None,
                "t": True
            },
            "i": "J"
        }
        self.assertEqual(actual, expected)
        self.assertNotEqual(actual, base)

    def test_load_full(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))
        uos.ADD_ENTRIES.append(("cache_full.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        config.CACHE_FILE_PATH = self.getAssetFilePath("cache_full.json")

        config.load()
        self.assertEqual(config.config.network.wifi.ssid, "WiFi-SSID")
        self.assertEqual(config.config.network.wifi.password, "WiFi-Password")
        self.assertEqual(config.config.network.ntp.server, "ntp.example.com")
        self.assertEqual(config.config.network.ntp.timezone, -12)
        self.assertEqual(config.config.b_route.id, "00000000000000000000000000000000")
        self.assertEqual(config.config.b_route.password, "XXXXXXXXXXXX")
        self.assertEqual(config.config.wattmeter.max.watt, 3000)
        self.assertEqual(config.config.wattmeter.warning.watt, 2500)
        self.assertTrue(config.config.wattmeter.warning.beep)
        self.assertEqual(config.config.wattmeter.caution.watt, 2000)
        self.assertTrue(config.config.wattmeter.caution.beep)
        self.assertEqual(config.config.wattmeter.update_interval, 15)
        self.assertEqual(config.config.wattmeter.beep_volume, 5)
        self.assertFalse(config.config.wattmeter.auto_reboot)
        self.assertTrue(config.config.wattmeter.sync_cache)
        self.assertEqual(config.config.display.brightness, 50)
        self.assertEqual(config.config.display.sleep.start, "23:00")
        self.assertEqual(config.config.display.sleep.end, "6:00")
        self.assertEqual(config.config.display.sleep.start_time, 82800)
        self.assertEqual(config.config.display.sleep.duration, 25200)

        self.assertEqual(config.cache.channel, "21")
        self.assertEqual(config.cache.pan_id, "8888")
        self.assertEqual(config.cache.mac_addr, "001D129012345678")
        self.assertEqual(config.cache.factor, 1)
        self.assertAlmostEqual(config.cache.unit, 0.1)
        self.assertEqual(config.cache.significant_figures, 6)
        self.assertTrue(config.cache.display_flip)
        self.assertEqual(config.cache.face_id, 1)

    def test_load_min(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

        config.load()
        self.assertIsNone(config.config.network.wifi)
        self.assertEqual(config.config.network.ntp.server, "ntp.nict.jp")
        self.assertEqual(config.config.network.ntp.timezone, 9)
        self.assertEqual(config.config.b_route.id, "00000000000000000000000000000000")
        self.assertEqual(config.config.b_route.password, "XXXXXXXXXXXX")
        self.assertEqual(config.config.wattmeter.max.watt, 3000)
        self.assertIsNone(config.config.wattmeter.warning)
        self.assertIsNone(config.config.wattmeter.caution)
        self.assertEqual(config.config.wattmeter.update_interval, 30)
        self.assertEqual(config.config.wattmeter.beep_volume, 3)
        self.assertTrue(config.config.wattmeter.auto_reboot)
        self.assertFalse(config.config.wattmeter.sync_cache)
        self.assertEqual(config.config.display.brightness, 50)
        self.assertIsNone(config.config.display.sleep)

        self.assertIsNone(config.cache.channel)
        self.assertIsNone(config.cache.pan_id)
        self.assertIsNone(config.cache.mac_addr)
        self.assertIsNone(config.cache.factor)
        self.assertIsNone(config.cache.unit)
        self.assertIsNone(config.cache.significant_figures)
        self.assertFalse(config.cache.display_flip)
        self.assertEqual(config.cache.face_id, 0)

    def test_load_keep_default_cache(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

        config.load()
        self.assertIsNone(config.DEFAULT_CACHE["channel"])
        self.assertIsNone(config.cache.channel)
        config.cache.channel = "21"
        self.assertIsNone(config.DEFAULT_CACHE["channel"])
        self.assertEqual(config.cache.channel, "21")

    def test_load_wifi_ssid_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wifi"] = {
                "password": "dummy"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wifi.ssid", str(cm.exception))
            self.assertIn("wifi.password", str(cm.exception))

    def test_load_wifi_password_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wifi"] = {
                "ssid": "dummy"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wifi.ssid", str(cm.exception))
            self.assertIn("wifi.password", str(cm.exception))

    def test_load_b_route_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            del config_min["b_route"]
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("b_route must be present", str(cm.exception))

    def test_load_b_route_id_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["b_route"] = {
                "password": "dummy"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("b_route.id", str(cm.exception))
            self.assertIn("b_route.password", str(cm.exception))

    def test_load_b_route_password_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["b_route"] = {
                "id": "dummy"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("b_route.id", str(cm.exception))
            self.assertIn("b_route.password", str(cm.exception))

    def test_load_b_route_id_not_str(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["b_route"]["id"] = 12345678901234567890123456789012
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("b_route.id must be a string", str(cm.exception))

    def test_load_b_route_id_invalid_length(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["b_route"]["id"] = "dummy"
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("b_route.id", str(cm.exception))
            self.assertIn("32", str(cm.exception))

    def test_load_b_route_password_not_str(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["b_route"]["password"] = 1234567890
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("b_route.password must be a string", str(cm.exception))

    def test_load_wattmeter_max_watt_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["max"]["watt"] = None
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.max.watt must be present", str(cm.exception))

    def test_load_wattmeter_max_watt_not_int(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["max"]["watt"] = "3000"
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.max.watt must be an integer", str(cm.exception))

    def test_load_wattmeter_max_watt_too_small(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["max"]["watt"] = 999
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.max.watt", str(cm.exception))
            self.assertIn("1000", str(cm.exception))
            self.assertIn("9999", str(cm.exception))

    def test_load_wattmeter_max_watt_too_large(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["max"]["watt"] = 10000
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.max.watt", str(cm.exception))
            self.assertIn("1000", str(cm.exception))
            self.assertIn("9999", str(cm.exception))

    def test_load_wattmeter_warning_watt_not_int(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["warning"] = {
                "watt": "1000"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.warning.watt must be an integer", str(cm.exception))

    def test_load_wattmeter_warning_watt_too_small(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["warning"] = {
                "watt": 0
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.warning.watt", str(cm.exception))
            self.assertIn("0", str(cm.exception))

    def test_load_wattmeter_warning_watt_too_large(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["warning"] = {
                "watt": config_min["wattmeter"]["max"]["watt"]
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.warning.watt", str(cm.exception))
            self.assertIn("wattmeter.max.watt", str(cm.exception))

    def test_load_wattmeter_caution_watt_not_int(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["caution"] = {
                "watt": "1000"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.caution.watt must be an integer", str(cm.exception))

    def test_load_wattmeter_caution_watt_too_small(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["caution"] = {
                "watt": 0
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.caution.watt", str(cm.exception))
            self.assertIn("0", str(cm.exception))

    def test_load_wattmeter_caution_watt_greater_than_max(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["caution"] = {
                "watt": config_min["wattmeter"]["max"]["watt"]
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.caution.watt", str(cm.exception))
            self.assertIn("wattmeter.max.watt", str(cm.exception))

    def test_load_wattmeter_caution_watt_greater_than_warning(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["wattmeter"]["warning"] = {
                "watt": 2000
            }
            config_min["wattmeter"]["caution"] = {
                "watt": 2500
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("wattmeter.caution.watt", str(cm.exception))
            self.assertIn("wattmeter.warning.watt", str(cm.exception))

    def test_load_wattmeter_display_brightness_not_int(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "brightness": "50"
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("display.brightness must be an integer", str(cm.exception))

    def test_load_wattmeter_display_brightness_too_small(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "brightness": -1
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("display.brightness", str(cm.exception))
            self.assertIn(" 0 ", str(cm.exception))
            self.assertIn("100", str(cm.exception))


    def test_load_wattmeter_display_brightness_too_large(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "brightness": 101
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("display.brightness", str(cm.exception))
            self.assertIn(" 0 ", str(cm.exception))
            self.assertIn("100", str(cm.exception))

    def test_load_wattmeter_display_sleep_start_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "end": "00:00"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("display.sleep.start", str(cm.exception))
            self.assertIn("must be present", str(cm.exception))

    def test_load_wattmeter_display_sleep_end_not_present(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:00"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("display.sleep.end", str(cm.exception))
            self.assertIn("must be present", str(cm.exception))

    def test_load_wattmeter_display_sleep_start_invalid_format_not_separated(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "0000",
                    "end": "23:59"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.start format", str(cm.exception))

    def test_load_wattmeter_display_sleep_start_invalid_format_not_decimal(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:FF",
                    "end": "23:59"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.start format", str(cm.exception))

    def test_load_wattmeter_display_sleep_start_hour_out_of_range(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "24:00",
                    "end": "23:59"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.start format", str(cm.exception))

    def test_load_wattmeter_display_sleep_start_minute_out_of_range(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:60",
                    "end": "23:59"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.start format", str(cm.exception))

    def test_load_wattmeter_display_sleep_end_invalid_format_not_separated(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:00",
                    "end": "2359"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.end format", str(cm.exception))

    def test_load_wattmeter_display_sleep_end_invalid_format_not_decimal(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:00",
                    "end": "AA:59"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.end format", str(cm.exception))

    def test_load_wattmeter_display_sleep_end_hour_out_of_range(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:00",
                    "end": "24:00"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.end format", str(cm.exception))

    def test_load_wattmeter_display_sleep_end_minute_out_of_range(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "00:00",
                    "end": "24:60"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("Invalid display.sleep.end format", str(cm.exception))

    def test_load_wattmeter_display_sleep_not_equal(self):
        uos.ADD_ENTRIES.append(("config_invalid.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_invalid.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "12:00",
                    "end": "12:00"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            with self.assertRaises(wmconfig.InvalidConfigError) as cm:
                config.load()
            self.assertIn("display.sleep.start", str(cm.exception))
            self.assertIn("display.sleep.end", str(cm.exception))
            self.assertIn("same", str(cm.exception))

    def test_calcSleepTime(self):
        uos.ADD_ENTRIES.append(("config_sleep.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_sleep.json")
            config.CONFIG_FILE_PATH = tmp_config_path
            config.CACHE_FILE_PATH = self.getAssetFilePath("notexists.json")

            config_min = self.getAssetJson("config_min.json")
            config_min["display"] = {
                "sleep": {
                    "start": "12:34",
                    "end": "12:35"
                }
            }
            with open(tmp_config_path, "w") as f:
                json.dump(config_min, f)

            config.load()
            self.assertEqual(config.config.display.sleep.start, "12:34")
            self.assertEqual(config.config.display.sleep.end, "12:35")
            self.assertEqual(config.config.display.sleep.start_time, 45240)
            self.assertEqual(config.config.display.sleep.duration, 60)

    def test_saveCache(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config_w = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config_r = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config_w.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        config_r.CONFIG_FILE_PATH = config_w.CONFIG_FILE_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            config_w.CACHE_FILE_PATH = os.path.join(tmpdir, "tmpcache.json")
            config_r.CACHE_FILE_PATH = config_w.CACHE_FILE_PATH

            config_w.load()
            config_w.cache.channel = "23"
            config_w.cache.pan_id = "4567"
            config_w.cache.mac_addr = "FFEEDDCCBBAA9988"
            config_w.cache.factor = 10
            config_w.cache.unit = 0.001
            config_w.cache.significant_figures = 8
            config_w.cache.display_flip = True
            config_w.cache.face_id = 2
            config_w.saveCache()

            self.assertTrue(os.path.isfile(config_w.CACHE_FILE_PATH))
            uos.ADD_ENTRIES.append(("tmpcache.json", 0x8000, 0))

            config_r.load()
            self.assertEqual(config_r.cache.channel, "23")
            self.assertEqual(config_r.cache.pan_id, "4567")
            self.assertEqual(config_r.cache.mac_addr, "FFEEDDCCBBAA9988")
            self.assertEqual(config_r.cache.factor, 10)
            self.assertAlmostEqual(config_r.cache.unit, 0.001)
            self.assertEqual(config_r.cache.significant_figures, 8)
            self.assertTrue(config_r.cache.display_flip)
            self.assertEqual(config_r.cache.face_id, 2)

    def test_saveCache_overwrite(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config_w = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config_r = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config_w.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        config_r.CONFIG_FILE_PATH = config_w.CONFIG_FILE_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            config_w.CACHE_FILE_PATH = os.path.join(tmpdir, "tmpcache.json")
            config_r.CACHE_FILE_PATH = config_w.CACHE_FILE_PATH

            self.assertFalse(os.path.isfile(config_w.CACHE_FILE_PATH))

            config_w.load()
            config_w.cache.channel = "23"
            config_w.cache.pan_id = "4567"
            config_w.cache.mac_addr = "FFEEDDCCBBAA9988"
            config_w.cache.factor = 10
            config_w.cache.unit = 0.01
            config_w.cache.display_flip = True
            config_w.cache.significant_figures = 6
            config_w.cache.face_id = 2
            config_w.saveCache()

            self.assertTrue(os.path.isfile(config_w.CACHE_FILE_PATH))
            uos.ADD_ENTRIES.append(("tmpcache.json", 0x8000, 0))

            config_w.cache.channel = "24"
            config_w.cache.pan_id = "4568"
            config_w.cache.mac_addr = "FFEEDDCCBBAA9989"
            config_w.cache.factor = 100
            config_w.cache.unit = 0.001
            config_w.cache.display_flip = False
            config_w.cache.significant_figures = 7
            config_w.cache.face_id = 3
            config_w.saveCache()

            config_r.load()
            self.assertEqual(config_r.cache.channel, "24")
            self.assertEqual(config_r.cache.pan_id, "4568")
            self.assertEqual(config_r.cache.mac_addr, "FFEEDDCCBBAA9989")
            self.assertEqual(config_r.cache.factor, 100)
            self.assertAlmostEqual(config_r.cache.unit, 0.001)
            self.assertEqual(config_r.cache.significant_figures, 7)
            self.assertFalse(config_r.cache.display_flip)
            self.assertEqual(config_r.cache.face_id, 3)

    def test_saveCacheIfChanged(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            config.CACHE_FILE_PATH = os.path.join(tmpdir, "tmpcache.json")

            self.assertFalse(os.path.isfile(config.CACHE_FILE_PATH))

            config.load()

            # デフォルト状態から変更がない場合は保存しない
            self.assertFalse(config.saveCacheIfChanged())
            self.assertFalse(os.path.isfile(config.CACHE_FILE_PATH))

            config.cache.channel = "23"
            config.cache.pan_id = "4567"
            config.cache.mac_addr = "FFEEDDCCBBAA9988"
            config.cache.factor = 10
            config.cache.unit = 0.01
            config.cache.display_flip = True
            config.cache.significant_figures = 6
            config.cache.face_id = 2
            self.assertTrue(config.saveCacheIfChanged())
            self.assertTrue(os.path.isfile(config.CACHE_FILE_PATH))

            config.cache.channel = "23"
            config.cache.pan_id = "4567"
            config.cache.mac_addr = "FFEEDDCCBBAA9988"
            config.cache.factor = 10
            config.cache.unit = 0.01
            config.cache.display_flip = True
            config.cache.significant_figures = 6
            config.cache.face_id = 2
            # 値の変更なし
            self.assertFalse(config.saveCacheIfChanged())

            config.cache.face_id = 3
            # 値の変更あり
            self.assertTrue(config.saveCacheIfChanged())

            self.assertEqual(config.cache.channel, "23")
            self.assertEqual(config.cache.pan_id, "4567")
            self.assertEqual(config.cache.mac_addr, "FFEEDDCCBBAA9988")
            self.assertEqual(config.cache.factor, 10)
            self.assertAlmostEqual(config.cache.unit, 0.01)
            self.assertEqual(config.cache.significant_figures, 6)
            self.assertTrue(config.cache.display_flip)
            self.assertEqual(config.cache.face_id, 3)

    def test_saveCacheIfChanged_rewrite_file(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config_w = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config_rw = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config_w.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        config_rw.CONFIG_FILE_PATH = config_w.CONFIG_FILE_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            config_w.CACHE_FILE_PATH = os.path.join(tmpdir, "tmpcache.json")
            config_rw.CACHE_FILE_PATH = config_w.CACHE_FILE_PATH

            self.assertFalse(os.path.isfile(config_w.CACHE_FILE_PATH))

            config_w.load()

            config_w.cache.channel = "23"
            config_w.cache.pan_id = "4567"
            config_w.cache.mac_addr = "FFEEDDCCBBAA9988"
            config_w.cache.factor = 10
            config_w.cache.unit = 0.01
            config_w.cache.display_flip = True
            config_w.cache.significant_figures = 6
            config_w.cache.face_id = 2
            self.assertTrue(config_w.saveCacheIfChanged())
            self.assertTrue(os.path.isfile(config_w.CACHE_FILE_PATH))

            uos.ADD_ENTRIES.append(("tmpcache.json", 0x8000, 0))
            config_rw.load()

            config_rw.cache.channel = "23"
            config_rw.cache.pan_id = "4567"
            config_rw.cache.mac_addr = "FFEEDDCCBBAA9988"
            config_rw.cache.factor = 10
            config_rw.cache.unit = 0.01
            config_rw.cache.display_flip = True
            config_rw.cache.significant_figures = 6
            config_rw.cache.face_id = 2
            # 値の変更なし
            self.assertFalse(config_rw.saveCacheIfChanged())

            config_rw.cache.face_id = 3
            # 値の変更あり
            self.assertTrue(config_rw.saveCacheIfChanged())

            self.assertEqual(config_rw.cache.channel, "23")
            self.assertEqual(config_rw.cache.pan_id, "4567")
            self.assertEqual(config_rw.cache.mac_addr, "FFEEDDCCBBAA9988")
            self.assertEqual(config_rw.cache.factor, 10)
            self.assertAlmostEqual(config_rw.cache.unit, 0.01)
            self.assertEqual(config_rw.cache.significant_figures, 6)
            self.assertTrue(config_rw.cache.display_flip)
            self.assertEqual(config_rw.cache.face_id, 3)

    def test_removeCache(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        config = wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            config.CACHE_FILE_PATH = os.path.join(tmpdir, "tmpcache.json")

            config.load()
            config.cache.channel = "23"
            config.cache.pan_id = "4567"
            config.cache.mac_addr = "FFEEDDCCBBAA9988"
            config.cache.display_flip = True
            config.cache.face_id = 2

            config.saveCache()
            self.assertTrue(os.path.isfile(config.CACHE_FILE_PATH))
            uos.ADD_ENTRIES.append(("tmpcache.json", 0x8000, 0))

            config.removeCache()
            self.assertFalse(os.path.isfile(config.CACHE_FILE_PATH))

class TestAttrDict(unittest.TestCase):
    def test_init(self):
        kv = {
            "attr1": 1,
            "attr2": "2",
            "attr3": [1, 2, 3],
            "attr4": {
                "sub1": 11,
                "sub2": "12",
                "sub3": [11, 12, 13],
                "sub4": [{}, {"sub4-1", "14"}]
            }
        }
        ad = wmconfig.AttrDict(kv)
        self.assertEqual(ad.attr1, 1)
        self.assertEqual(ad.attr2, "2")
        self.assertEqual(ad.attr3, [1, 2, 3])
        self.assertEqual(ad.attr4.sub1, 11)
        self.assertEqual(ad.attr4.sub2, "12")
        self.assertEqual(ad.attr4.sub3, [11, 12, 13])
        self.assertEqual(ad.attr4.sub4, [{}, {"sub4-1", "14"}])

    def test_getattr(self):
        kv = {
            "attr1": 1
        }
        ad = wmconfig.AttrDict(kv)
        self.assertEqual(ad.attr1, 1)
        self.assertIsNone(ad.attr2)

    def test_eq(self):
        kv1 = {
            "attr1": 1,
            "attr2": [1, 2, 3],
            "attr3": {
                "sub1": 11,
                "sub2": "12",
            }
        }
        kv2 = {
            "attr1": 1,
            "attr2": [1, 2, 3],
            "attr3": {
                "sub1": 11,
                "sub2": "12",
            }
        }
        kv3 = {
            "attr1": 1,
            "attr2": [1, 2, 3],
            "attr3": {
                "sub1": 11,
                "sub2": 12,  # "12" → 12
            }
        }
        ad1 = wmconfig.AttrDict(kv1)
        ad2 = wmconfig.AttrDict(kv2)
        ad3 = wmconfig.AttrDict(kv3)
        self.assertTrue(ad1 == ad2)
        self.assertTrue(ad1 == kv2)
        self.assertFalse(ad1 == ad3)
        self.assertFalse(ad1 == kv3)
        self.assertFalse(ad1 == "ad1")

    def test_getDict(self):
        kv1 = {
            "attr1": 1,
            "attr2": [1, 2, 3],
            "attr3": {
                "sub1": 11,
                "sub2": "12",
                "sub3": {
                    "sub3-1": 111
                }
            }
        }
        kv2 = {
            "attr1": 1,
            "attr2": [1, 2, 3],
            "attr3": {
                "sub1": 11,
                "sub2": "12",
                "sub3": {
                    "sub3-1": 111
                }
            }
        }
        ad1 = wmconfig.AttrDict(kv1)
        actual = ad1.getDict()
        self.assertEqual(actual, kv2)
        self.assertIsInstance(actual, dict)
        self.assertEqual(actual["attr3"], kv2["attr3"])
        self.assertIsInstance(actual["attr3"], dict)
        self.assertEqual(actual["attr3"]["sub3"], kv2["attr3"]["sub3"])
        self.assertIsInstance(actual["attr3"]["sub3"], dict)
