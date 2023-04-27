import unittest
from unittest.mock import MagicMock, call
from mock import lcd, axp, ujson, uos, utime, logging, wifiCfg, ntptime, speaker
from mock.machine import UART
import os, tempfile, json
import vlcd, wisun, wmconfig, meter

class TestM5Wattmeter(unittest.TestCase):
    def getAssetFilePath(self, file_name):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", file_name)

    def getInstance(self):
        return meter.M5Wattmeter(
            vlcd=vlcd.VirtualLCD(lcd=lcd, axp=axp),
            client=wisun.BP35A1Client(uart=UART, utime=utime, logging=logging),
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging),
            logging=logging,
            wifiCfg=wifiCfg,
            utime=utime,
            ntptime=ntptime,
            speaker=speaker
        )

    def setUp(self):
        uos.ADD_ENTRIES = []

    def tearDown(self):
        utime.timestamp = None

    def test_addTask_getTask(self):
        def nothing():
            pass
        wm = self.getInstance()
        wm.addTask(
            launch_time=12445,
            func=nothing,
            interval=None
        )
        wm.addTask(
            launch_time=12345,
            func=nothing,
            interval=300
        )
        wm.addTask(
            launch_time=12545,
            func=nothing,
            interval=10
        )
        wm.addTask(
            launch_time=12645,
            func=nothing,
            interval=1
        )

        self.assertIsNone(wm._getTask(12344))
        self.assertEqual(wm._getTask(12345), {"t": 12345, "f": nothing, "i": 300})
        self.assertIsNone(wm._getTask(12345))
        self.assertEqual(wm._getTask(12555), {"t": 12445, "f": nothing, "i": None})
        self.assertEqual(wm._getTask(12555), {"t": 12545, "f": nothing, "i": 10})

    def test_execLaunchableTask(self):
        task1 = MagicMock()
        task2 = MagicMock()
        task3 = MagicMock()

        wm = self.getInstance()
        wm.addTask(
            launch_time=12355,
            func=task2,
            interval=300
        )
        wm.addTask(
            launch_time=12345,
            func=task1,
            interval=30
        )
        wm.addTask(
            launch_time=12360,
            func=task3,
            interval=5
        )

        # 12344 → None
        utime.timestamp = 12344
        self.assertFalse(wm.execLaunchableTask())
        # 12345 → 12345
        utime.timestamp = 12345
        self.assertTrue(wm.execLaunchableTask())
        self.assertEqual(task1.call_count, 1)
        self.assertEqual(task2.call_count, 0)
        self.assertEqual(task3.call_count, 0)
        # 12360 → 12355, (12360)
        utime.timestamp = 12360
        self.assertTrue(wm.execLaunchableTask())
        self.assertEqual(task1.call_count, 1)
        self.assertEqual(task2.call_count, 1)
        self.assertEqual(task3.call_count, 0)
        # 12361 → 12360
        utime.timestamp = 12361
        self.assertTrue(wm.execLaunchableTask())
        self.assertEqual(task1.call_count, 1)
        self.assertEqual(task2.call_count, 1)
        self.assertEqual(task3.call_count, 1)
        # 12365 → None
        utime.timestamp = 12365
        self.assertFalse(wm.execLaunchableTask())
        # 12366 → 12366(12360の繰り返し)
        utime.timestamp = 12366
        self.assertTrue(wm.execLaunchableTask())
        self.assertEqual(task1.call_count, 1)
        self.assertEqual(task2.call_count, 1)
        self.assertEqual(task3.call_count, 2)

    def test_toggleSleep(self):
        wm = self.getInstance()
        axp.setLcdBrightness = MagicMock()

        axp.setLcdBrightness.reset_mock()
        self.assertTrue(wm.toggleSleep())
        axp.setLcdBrightness.assert_called_once_with(0)

        axp.setLcdBrightness.reset_mock()
        self.assertFalse(wm.toggleSleep())
        axp.setLcdBrightness.assert_called_once_with(60)

    def test_toggleFlip(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))
        uos.ADD_ENTRIES.append(("cache_full.json", 0x8000, 0))

        wm = self.getInstance()
        wm.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        wm.config.CACHE_FILE_PATH = self.getAssetFilePath("cache_full.json")
        wm.config.load()

        self.assertTrue(wm.config.cache.display_flip)
        wm.toggleFlip()
        self.assertFalse(wm.config.cache.display_flip)
        wm.toggleFlip()
        self.assertTrue(wm.config.cache.display_flip)

    def test_addScheduledSleepTask(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))
        uos.ADD_ENTRIES.append(("cache_full.json", 0x8000, 0))

        wm = self.getInstance()
        wm.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        wm.config.CACHE_FILE_PATH = self.getAssetFilePath("cache_full.json")
        wm.config.load()
        # 23:00 - 06:00

        utime.timestamp = 734050799  # 2023/4/5 22:59:59
        wm._addScheduledSleepTask()
        self.assertEqual(wm._tasks[-1]["t"], 734050800)  # 2023/4/5 23:00:00
        utime.timestamp = 734050800  # 2023/4/5 23:00:00
        wm._tasks[-1]["f"]()
        self.assertEqual(wm._tasks[-1]["t"], 734076000)  # 2023/4/6 06:00:00
        utime.timestamp = 734076000  # 2023/4/6 06:00:00
        wm._tasks[-1]["f"]()
        self.assertEqual(wm._tasks[-1]["t"], 734137200)  # 2023/4/6 23:00:00

    def test_addScheduledSleepTask_same_day(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))
        uos.ADD_ENTRIES.append(("cache_full.json", 0x8000, 0))

        wm = self.getInstance()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_config_path = os.path.join(tmpdir, "config_sleep_same_day.json")
            with open(self.getAssetFilePath("config_full.json"), "r") as f:
                config_full = json.load(f)
            config_full["display"]["sleep"]["start"] = "12:00"
            config_full["display"]["sleep"]["end"] = "12:01"
            with open(tmp_config_path, "w") as f:
                json.dump(config_full, f)

            wm.config.CONFIG_FILE_PATH = tmp_config_path
            wm.config.CACHE_FILE_PATH = self.getAssetFilePath("cache_full.json")
            wm.config.load()
            # 12:00 - 12:01

        utime.timestamp = 734011199  # 2023/4/5 11:59:59
        wm._addScheduledSleepTask()
        self.assertEqual(wm._tasks[-1]["t"], 734011200)  # 2023/4/5 12:00:00
        utime.timestamp = 734011200  # 2023/4/5 12:00:00
        wm._tasks[-1]["f"]()
        self.assertEqual(wm._tasks[-1]["t"], 734011260)  # 2023/4/5 12:01:00
        utime.timestamp = 734011260  # 2023/4/5 12:01:00
        wm._tasks[-1]["f"]()
        self.assertEqual(wm._tasks[-1]["t"], 734097600)  # 2023/4/6 12:00:00

    def test_beep(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))
        uos.ADD_ENTRIES.append(("cache_full.json", 0x8000, 0))

        wm = self.getInstance()
        wm.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        wm.config.CACHE_FILE_PATH = self.getAssetFilePath("cache_full.json")
        wm.config.load()

        speaker.setVolume = MagicMock()
        speaker.tone = MagicMock()
        utime.sleep_ms = MagicMock()

        wm.beep(
            (100, 200),
            (None, 300),
            (400, 500)
        )
        speaker.setVolume.assert_called_once_with(5)
        speaker.tone.assert_has_calls([call(100, 200), call(400, 500)])
        utime.sleep_ms.assert_called_once_with(300)

class TestWMState(unittest.TestCase):
    def getAssetFilePath(self, file_name):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", file_name)

    def setUp(self):
        uos.ADD_ENTRIES = []

    def test_getTime(self):
        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.setTime((2020, 1, 2, 3, 4, 5, 4, 2))
        self.assertEqual(state.getTime(), "2020/1/2 03:04")

    def test_getTime_with_format(self):
        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.setTime((2020, 1, 2, 3, 4, 5, 4, 2))
        actual = state.getTime("{year:d}-{mon:02d}-{mday:02d} {hour:02d}:{min:02d}:{sec:02d}")
        self.assertEqual(actual, "2020-01-02 03:04:05")

    def test_getCurrentWatt(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))

        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        state.config.load()

        self.assertEqual(state.getCurrentWatt(), 0)
        state.setCurrentWatt(123)
        self.assertEqual(state.getCurrentWatt(), 123)

    def test_isStatusNormal_Caution_Warning(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        state.config.load()

        # caution, warning未設定
        state.setCurrentWatt(9999)
        self.assertTrue(state.isStatusNormal())
        self.assertFalse(state.isStatusCaution())
        self.assertFalse(state.isStatusWarning())

        state.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        state.config.load()
        # caution: 2000, warning: 2500

        state.setCurrentWatt(1999)
        self.assertTrue(state.isStatusNormal())
        self.assertFalse(state.isStatusCaution())
        self.assertFalse(state.isStatusWarning())

        state.setCurrentWatt(2000)
        self.assertFalse(state.isStatusNormal())
        self.assertTrue(state.isStatusCaution())
        self.assertFalse(state.isStatusWarning())

        state.setCurrentWatt(2499)
        self.assertFalse(state.isStatusNormal())
        self.assertTrue(state.isStatusCaution())
        self.assertFalse(state.isStatusWarning())

        state.setCurrentWatt(2500)
        self.assertFalse(state.isStatusNormal())
        self.assertFalse(state.isStatusCaution())
        self.assertTrue(state.isStatusWarning())

        state.setCurrentWatt(3000)
        self.assertFalse(state.isStatusNormal())
        self.assertFalse(state.isStatusCaution())
        self.assertTrue(state.isStatusWarning())

        state.setCurrentWatt(2499)
        self.assertFalse(state.isStatusNormal())
        self.assertTrue(state.isStatusCaution())
        self.assertFalse(state.isStatusWarning())

        state.setCurrentWatt(1999)
        self.assertTrue(state.isStatusNormal())
        self.assertFalse(state.isStatusCaution())
        self.assertFalse(state.isStatusWarning())

    def test_reportError(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        state.config.load()

        for i in range(1, 10):
            e = Exception("Error " + str(i))
            state.reportError(e)

        ex = Exception("Error 10")
        with self.assertRaises(Exception) as cm:
            state.reportError(ex)
        self.assertEqual(cm.exception, ex)

    def test_reportError_cut_in_success(self):
        uos.ADD_ENTRIES.append(("config_min.json", 0x8000, 0))

        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_min.json")
        state.config.load()

        for i in range(1, 10):
            e = Exception("Error " + str(i))
            state.reportError(e)

        state.setCurrentWatt(123)

        ex = Exception("Error 10")
        state.reportError(ex)
        # not raised

    def test_isStatusEscalated(self):
        uos.ADD_ENTRIES.append(("config_full.json", 0x8000, 0))

        state = meter.WMState(
            config=wmconfig.WMConfig(ujson=ujson, uos=uos, logging=logging)
        )
        state.config.CONFIG_FILE_PATH = self.getAssetFilePath("config_full.json")
        state.config.load()
        # caution: 2000, warning: 2500

        self.assertFalse(state.isStatusEscalated())

        # Normal -> Normal
        state.setCurrentWatt(1000)
        self.assertFalse(state.isStatusEscalated())

        # Normal -> Caution
        state.setCurrentWatt(2000)
        self.assertTrue(state.isStatusEscalated())
        self.assertFalse(state.isStatusEscalated())

        # Caution -> Caution
        state.setCurrentWatt(2499)
        self.assertFalse(state.isStatusEscalated())

        # Caution -> Warning
        state.setCurrentWatt(2500)
        self.assertTrue(state.isStatusEscalated())
        self.assertFalse(state.isStatusEscalated())

        # Warning -> Warning
        state.setCurrentWatt(2500)
        self.assertFalse(state.isStatusEscalated())

        # Warning -> Caution
        state.setCurrentWatt(2499)
        self.assertFalse(state.isStatusEscalated())

        # Caution -> Normal
        state.setCurrentWatt(1999)
        self.assertFalse(state.isStatusEscalated())

        # Normal -> Warning
        state.setCurrentWatt(3000)
        self.assertTrue(state.isStatusEscalated())
        self.assertFalse(state.isStatusEscalated())

        # Warning -> Normal
        state.setCurrentWatt(0)
        self.assertFalse(state.isStatusEscalated())

        # Normal -> Caution -> Normal
        state.setCurrentWatt(0)
        state.setCurrentWatt(2000)
        state.setCurrentWatt(1000)
        self.assertFalse(state.isStatusEscalated())

        # Normal -> Warning -> Caution
        state.setCurrentWatt(0)
        state.setCurrentWatt(3000)
        state.setCurrentWatt(2500)
        self.assertTrue(state.isStatusEscalated())
        self.assertFalse(state.isStatusEscalated())
