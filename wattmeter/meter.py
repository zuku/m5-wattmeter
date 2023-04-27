# meter >>>

class M5Wattmeter:
    """
    M5 Wattmeterのアプリケーションクラス

    M5 Wattmeterのアプリケーションとしての処理を行うクラス

    Examples
    --------
    from m5stack import lcd, axp, speaker
    from machine import UART
    import utime, ujson, uos, wifiCfg, ntptime
    from wmlogging import Logger as logging

    logging.basicConfig(
        utime=utime,
        level=logging.INFO
    )

    wm = M5Wattmeter(
        vlcd=VirtualLCD(lcd=lcd, axp=axp),
        client=BP35A1Client(uart=UART, utime=utime, logging=logging),
        config=WMConfig(ujson=ujson, uos=uos, logging=logging),
        logging=logging,
        wifiCfg=wifiCfg,
        utime=utime,
        ntptime=ntptime,
        speaker=speaker
    )

    wm.prepare()
    wm.startTaskLoop()

    Attributes
    ----------
    WIFI_CONNECT_TIMEOUT : int
        WiFi接続時の接続待ち時間(秒)
        指定の時間までWiFi接続を試みる
    WIFI_CONNECT_RETRY : int
        WiFi接続のリトライ回数
        指定の回数WiFi接続を試みる
    SCAN_PRE_WAIT_SEC : int
        execScan() (SKSCAN)実行前に待機する時間(秒)
        スマートメータに対して続けてコマンドを送り続けるとSKSCANが失敗しやすい気がするため指定秒数待機する
        呪術的設定
    SCAN_RETRY : int
        execScan() (SKSCAN)失敗時のリトライ回数
    JOIN_RETRY : int
        execJoin() (SKJOIN)失敗時のリトライ回数
    TASK_LOOP_WAIT_SEC : int
        タスク実行ループの1ループごとの待機時間(秒)
    NTP_UPDATE_INTERVAL : int
        NTPとの時刻同期を行う間隔(秒)
    DISPLAY_UPDATE_INTERVAL : int
        ディスプレイ(LCD)の表示を更新する間隔(秒)
    CACHE_SYNC_DELAY : int
        キャッシュを書き込むまでの遅延時間(秒)
        ボタンを押して表示を切り替えた後に設定内容をキャッシュに書き込むまでの待機時間
        ボタンが続けて押された場合に都度キャッシュ書き込みが行われないよう待機する
    """

    WIFI_CONNECT_TIMEOUT = 15
    WIFI_CONNECT_RETRY = 3

    SCAN_PRE_WAIT_SEC = 5
    SCAN_RETRY = 3

    JOIN_RETRY = 3

    NTP_UPDATE_INTERVAL = 86400  # 24時間
    DISPLAY_UPDATE_INTERVAL = 5

    CACHE_SYNC_DELAY = 60

    def __init__(self, *, vlcd, client, config, logging, wifiCfg, utime, ntptime, speaker):
        """
        Parameters
        ----------
        vlcd : object
            VirtualLCDクラスインスタンス
        client : object
            BP35A1Clientクラスインタンス
        config : object
            WMConfigクライアントクラス
        logging : object
            Loggerクラス
        wifiCfg : object
            wifiCgfモジュール
        utime : object
            utimeモジュール
        ntptime : object
            ntptimeモジュール
        speaker : object
            m5stack.speaker
        """
        self.vlcd = vlcd
        self.client = client
        self.config = config
        self.logging = logging
        self.wificfg = wifiCfg
        self.utime = utime
        self.ntptime = ntptime
        self.speaker = speaker

        self.ntp_client = None
        self._tasks = []
        self._state = WMState(config=config)
        self._display_sleep = False
        self._scheduled_sleeping = False
        self._prepared = False

    def _prepareWiFi(self):
        """
        WiFi接続を行う

        Raises
        ------
        NetworkError
            WiFiへの接続に失敗した場合に発生する
        """
        config = self.config
        wificfg = self.wificfg
        utime = self.utime
        logger = self.logging
        if wificfg.is_connected():
            logger.info("WiFi already connected.")
            return
        if config.config.network.wifi is None:
            logger.debug("Use device WiFi settings.")
            ssid, password = wificfg.deviceCfg.get_wifi()
        else:
            ssid = config.config.network.wifi.ssid
            password = config.config.network.wifi.password

        logger.debug("Connect to WiFi. ssid: " + ssid)
        for _ in range(self.WIFI_CONNECT_RETRY + 1):
            wificfg.connect(ssid, password, timeout=self.WIFI_CONNECT_TIMEOUT, block=False)
            utime.sleep(self.WIFI_CONNECT_TIMEOUT + 1)
            if wificfg.is_connected():
                break
            logger.info("Retry WiFi connection.")
        if not wificfg.is_connected():
            raise NetworkError("Can not connect to WiFi")

    def _prepareNtp(self):
        """
        NTPによる時刻合わせを行う

        NTPによる時刻合わせを行い定期的な時刻修正を設定する
        """
        ntp_config = self.config.config.network.ntp
        self.logging.info("NTP server is " + ntp_config.server)
        self.ntp_client = self.ntptime.client(host=ntp_config.server, timezone=ntp_config.timezone)

    def _updateTime(self):
        """
        NTPによる時刻の更新(再同期)を行う
        """
        self.logging.info("Resync time.")
        try:
            if not self.wificfg.is_connected():
                self._prepareWiFi()
            self.ntp_client.updateTime()
        except Exception as e:
            # 一度時刻同期していれば大幅に狂うことはないという前提で
            # エラーの記録だけ行いタスクループの停止(例外の送出)はしない
            self.logging.e(e)

    def _prepareClient(self):
        """
        Wi-SUNクライアントの使用準備を行う

        Raises
        ------
        WiSUNError
            Wi-SUNデバイスが動作していない場合に発生する
        """
        total_steps = 5 + 18
        self.logging.info("Wi-SUN device check")
        self.vlcd.showProgress(5 / total_steps, "Wi-SUN device setup")
        self.client.clearBuffer()
        if not self.client.isDeviceAvailable():
            raise WiSUNError("Unavailable Wi-SUN device")
        self.logging.info("BP35A1 echo back off")
        self.vlcd.showProgress(6 / total_steps, "Set echo back off")
        self.client.execEchoBack(False)
        self.logging.info("BP35A1 ascii mode")
        self.vlcd.showProgress(7 / total_steps, "Set ascii mode")
        self.client.execSetAsciiMode()
        self.logging.info("BP35A1 terminate session")
        self.vlcd.showProgress(8 / total_steps, "Reset session")
        self.client.execTerminateSession()
        self.logging.info("BP35A1 set B-route password")
        self.vlcd.showProgress(9 / total_steps, "Set B-route password")
        self.client.execSetPwd(self.config.config.b_route.password)
        self.logging.info("BP35A1 set B-route id")
        self.vlcd.showProgress(10 / total_steps, "Set B-route ID")
        self.client.execSetRbId(self.config.config.b_route.id)

        cache = self.config.cache
        if None in (cache.channel, cache.pan_id, cache.mac_addr):
            self.logging.info("cache miss: scan results")
            self.vlcd.showProgress(11 / total_steps, "Scanning...")
            self.utime.sleep(self.SCAN_PRE_WAIT_SEC)
            retry_count = self.SCAN_RETRY
            while True:
                try:
                    self.logging.info("BP35A1 scan")
                    scan_results = self.client.execScan()
                    cache.channel  = scan_results["Channel"]
                    cache.pan_id   = scan_results["Pan ID"]
                    cache.mac_addr = scan_results["Addr"]
                    break
                except Exception as e:
                    self.logging.exception(e)
                    if retry_count > 0:
                        retry_count -= 1
                        self.logging.info("BP35A1 scan retry: " + str(retry_count))
                        continue
                    raise e
            self.vlcd.showProgress(12 / total_steps, "Scan complete")
            self.client.clearBuffer()

        self.logging.info("BP35A1 set channel: " + cache.channel)
        self.vlcd.showProgress(13 / total_steps, "Set channel")
        self.client.execSetChannel(cache.channel)
        self.logging.info("BP35A1 set Pan ID: " + cache.pan_id)
        self.vlcd.showProgress(14 / total_steps, "Set Pan ID")
        self.client.execSetPanId(cache.pan_id)
        self.logging.info("BP35A1 convert address: " + cache.mac_addr)
        self.vlcd.showProgress(15 / total_steps, "Convert address")
        ipv6_addr = self.client.execConvertAddress(cache.mac_addr)
        self.logging.info("BP35A1 IPv6 address: " + ipv6_addr)
        self.logging.info("BP35A1 join")
        self.vlcd.showProgress(16 / total_steps, "Connect to the meter...")
        retry_count = self.JOIN_RETRY
        while True:
            try:
                self.client.execJoin(ipv6_addr)
                break
            except Exception as e:
                self.logging.exception(e)
                if retry_count > 0:
                    retry_count -= 1
                    self.logging.info("BP35A1 join retry: " + str(retry_count))
                    continue
                raise e
        self.vlcd.showProgress(17 / total_steps, "Connected")

        self.logging.info("BP35A1 get meter status")
        self.vlcd.showProgress(18 / total_steps, "Get status")
        if not self.client.execGetStatus():
            raise WiSUNError("Unavailable smart meter")
        if cache.factor is None:
            self.logging.info("cache miss: factor")
            self.vlcd.showProgress(19 / total_steps, "Get factor")
            cache.factor = self.client.execGetFactor()
            self.logging.debug("factor: " + str(cache.factor))
        if cache.unit is None:
            self.logging.info("cache miss: unit")
            self.vlcd.showProgress(20 / total_steps, "Get unit")
            cache.unit = self.client.execGetIntegralPowerConsumptionUnit()
            self.logging.debug("unit: " + str(cache.unit))
        if cache.significant_figures is None:
            self.logging.info("cache miss: significant figures")
            self.vlcd.showProgress(21 / total_steps, "Get figures")
            cache.significant_figures = self.client.execGetSignificantFigures()
            self.logging.debug("significant figures: " + str(cache.significant_figures))

        self.vlcd.showProgress(22 / total_steps, "Device ready")
        self.client.setPowerConsumptionCalcParams(factor=cache.factor, unit=cache.unit)
        self.config.saveCacheIfChanged()

    def _prepareTask(self):
        """
        初期状態のタスクを準備する
        """
        # 時刻定期更新タスク
        self.addTask(
            launch_time=self.utime.time()+self.NTP_UPDATE_INTERVAL,
            func=self._updateTime,
            interval=self.NTP_UPDATE_INTERVAL
        )
        # 消費電力量取得
        self.addTask(
            launch_time=10,
            func=self._updateCurrentPowerConsumption,
            interval=self.config.config.wattmeter.update_interval
        )
        # ディスプレイ更新
        self.addTask(
            launch_time=11,
            func=self._updateDisplay,
            interval=self.DISPLAY_UPDATE_INTERVAL
        )
        # sleep設定
        self._addScheduledSleepTask()

    def prepare(self):
        """
        アプリケーションの実行準備を行う

        * 設定の読み込み
        * ネットワークの準備
          * Wi-Fi接続
          * NTPによる時刻合わせ
        * Wi-SUNクライアントの準備
        """
        total_steps = 5 + 18

        self.logging.info(">>> config.load()")
        self.config.load()
        self.logging.info("<<< config.load()")

        self.vlcd.setFlip(self.config.cache.display_flip)
        self.logging.debug("Display brightness: " + str(self.config.config.display.brightness))
        self.vlcd.setBrightness(self.config.config.display.brightness)
        self.logging.debug("Display face ID: " + str(self.config.cache.face_id))
        self.vlcd.setFace(self.config.cache.face_id)
        self.vlcd.showProgress(1 / total_steps, "Config loaded")

        self.logging.info(">>> _prepareWifi()")
        self.vlcd.showProgress(2 / total_steps, "WiFi connecting...")
        self._prepareWiFi()
        self.vlcd.showProgress(3 / total_steps, "WiFi connected")
        self.logging.info("<<< _prepareWifi()")

        self.logging.info(">>> _prepareNtp()")
        self._prepareNtp()
        self.vlcd.showProgress(4 / total_steps, "Time adjustment is completed")
        self.logging.info("<<< _prepareNtp()")

        self.logging.info(">>> _prepareClient()")
        self._prepareClient()
        self.logging.info("<<< _prepareClient()")

        self.logging.info(">>> _prepareTask()")
        self._prepareTask()
        self.vlcd.showProgress(23 / total_steps, "Ready")
        self.logging.info("<<< _prepareTask()")
        self._prepared = True

    def _updateDisplay(self):
        """
        外部への表示内容の更新を行う

        現在の状態をもとにディスプレイ表示の更新を行う
        表示内容に変化があると更新するのではなく定期的に現在(最新)の状態をもとに更新する
        メソッド名は"display"だがBeep音もここで鳴らしている

        現在の状態が注意や警告に悪化した場合は
        * 設定されたスリープ時間の場合 → 何もしない
        * ディスプレイが消灯している場合 → 点灯する
        * Beepの設定がある → Beep音を鳴らす
        """
        self._state.setTime(self.utime.localtime())
        self.vlcd.update(self._state)

        if self._scheduled_sleeping:
            return
        if not self._state.isStatusEscalated():
            return
        if self._display_sleep:
            self.toggleSleep()  # Wake up

        if self._state.isStatusCaution():
            if self.config.config.wattmeter.caution and self.config.config.wattmeter.caution.beep:
                # Caution beep
                self.beep((523, 100), (None, 80), (659, 100))
        elif self._state.isStatusWarning():
            if self.config.config.wattmeter.warning and self.config.config.wattmeter.warning.beep:
                # Warning beep
                self.beep((523, 100), (None, 80), (659, 100), (None, 80), (784, 100))

    def _updateCurrentPowerConsumption(self):
        """
        現在の消費電力量を更新する

        現在の消費電力量を取得して更新する
        """
        try:
            self._state.setCurrentWatt(self.client.execGetCurrentPowerConsumption())
        except Exception as e:
            self._state.reportError(e)
            self.logging.exception(e)

    def _addScheduledSleepTask(self):
        """
        時間によるディスプレイの消灯/点灯タスクを追加する
        """
        sleep = self.config.config.display.sleep
        if sleep is None:
            return
        timestamp = self.utime.time()
        year, month, mday, *_ = self.utime.localtime(timestamp)
        # 今日の00:00のタイムスタンプ取得(曜日と通算日数は適当で良いらしい)
        day_start_timestamp = self.utime.mktime((year, month, mday, 0, 0, 0, 0, 0))
        if day_start_timestamp + sleep.start_time > timestamp:
            # スリープ開始時刻以前→スリープタスク追加
            self.addTask(
                launch_time=day_start_timestamp + sleep.start_time,
                func=self.scheduledSleep,
                interval=None
            )
        elif day_start_timestamp + sleep.start_time + sleep.duration > timestamp:
            # スリープ開始時刻以降終了時刻未満→ウェイクアップタスク追加
            self.addTask(
                launch_time=day_start_timestamp + sleep.start_time + sleep.duration,
                func=self.scheduledWakeUp,
                interval=None
            )
        else:
            # スリープ終了時刻以降→翌日のスリープタスク追加
            self.addTask(
                launch_time=day_start_timestamp + sleep.start_time + 86400,
                func=self.scheduledSleep,
                interval=None
            )

    def _getTask(self, time):
        """
        指定した時間で実行すべきタスクをひとつ取得する

        指定した時間で実行すべきタスクをひとつ取得し待機中のタスクリストから削除する

        Parameters
        ----------
        time : int
            タイムスタンプ
            起動時刻が指定タイムスタンプ以前の最も起動時間が小さいタスクをひとつ取得する

        Returns
        -------
        dict | None
            実行すべきタスク
            タスクがない場合はNone
        """
        if len(self._tasks) < 1:
            return None
        if self._tasks[0]["t"] > time:
            return None
        return self._tasks.pop(0)

    def addTask(self, *, launch_time, func, interval=None):
        """
        タスクを追加する

        Parameters
        ----------
        launch_time : int
            タスクを実行するタイムスタンプ
            即座(次のループ)に実行したい場合は0など十分に小さい数を指定する
        func : function
            実行するタスクの関数
            例外のハンドリングは関数内で行う(例外が投げられると以後の処理は全て止まる)
        interval : int | None
            タスクを繰り返し実行する場合の間隔
            指定した秒数の間隔でタスクを繰り返し実行する
            間隔はタスクの実行開始時から計算される(launch_timeや終了時点してからではない)
            Noneの場合は繰り返さない(1度だけ実行)
        """
        task = {
            "t": launch_time,
            "f": func,
            "i": interval
        }
        self.logging.debug(task)
        self._tasks.append(task)
        self._tasks.sort(key=lambda task: task["t"])

    def execLaunchableTask(self):
        """
        現時点で起動可能なタスクを実行する

        Returns
        -------
        bool
            タスクが実行された場合はTrue
            実行すべきタスクがなかった場合はFalse
        """
        timestamp = self.utime.time()
        task = self._getTask(timestamp)
        if task is None:
            return False
        self.logging.debug(timestamp)
        try:
            task["f"]()
        finally:
            if task["i"] is not None:
                self.addTask(
                    launch_time=timestamp+task["i"],
                    func=task["f"],
                    interval=task["i"]
                )
        return True

    def toggleSleep(self):
        """
        ディスプレイの点灯と消灯を交互に切り替える

        Returns
        -------
        bool
            消灯(sleep)状態に変更された場合はTrue
        """
        if self._display_sleep:
            self.logging.info("Wake up")
            self.vlcd.wakeUp()
        else:
            self.logging.info("Sleep")
            self.vlcd.sleep()
        self._display_sleep = not self._display_sleep
        return self._display_sleep

    def scheduledSleep(self):
        """
        時間によるディスプレイの消灯
        """
        self.logging.info("Scheduled sleep")
        self.vlcd.sleep()
        self._display_sleep = True
        self._scheduled_sleeping = True
        self._addScheduledSleepTask()

    def scheduledWakeUp(self):
        """
        時間によるディスプレイの点灯
        """
        self.logging.info("Scheduled wake up")
        self.vlcd.wakeUp()
        self._display_sleep = False
        self._scheduled_sleeping = False
        self._addScheduledSleepTask()

    def toggleFlip(self):
        """
        ディスプレイの上下を反転する

        ディスプレイ表示の上下を反転する
        準備が完了(タスク処理ループ中)している場合は明示的にディスプレイを再描画する
        """
        flip = not self.config.cache.display_flip
        self.logging.info("Flip display: " + str(flip))
        self.vlcd.setFlip(flip)
        self.config.cache.display_flip = flip
        if self._prepared:
            self._updateDisplay()
        if self.config.config.wattmeter.sync_cache:
            self.addTask(
                launch_time=self.utime.time()+self.CACHE_SYNC_DELAY,
                func=self.config.saveCacheIfChanged,
                interval=None
            )

    def beep(self, *args):
        """
        スピーカーからビープ音を鳴らす

        Parameters
        ----------
        tuple (int, int), (int, int), ...
            周波数と継続時間のtuple
            (440, 500): 440Hzを500ms鳴らす
            (None, 100): 100ms無音(sleep)
        """
        self.logging.debug("Speaker volume: " + str(self.config.config.wattmeter.beep_volume))
        self.logging.debug(args)
        self.speaker.setVolume(self.config.config.wattmeter.beep_volume)
        for note in args:
            if note[0] is None:
                self.utime.sleep_ms(note[1])
            else:
                self.speaker.tone(*note)

    def switchFace(self):
        """
        次の表示に切り替える

        ディスプレイの表示形式を次の形式に切り替える
        準備が完了(タスク処理ループ中)している場合は明示的にディスプレイを再描画する
        """
        face_id = self.vlcd.nextFace()
        self.logging.info("Display face: " + str(face_id))
        self.vlcd.setFace(face_id)
        if self._prepared:
            self._updateDisplay()
        if self.config.config.wattmeter.sync_cache:
            self.addTask(
                launch_time=self.utime.time()+self.CACHE_SYNC_DELAY,
                func=self.config.saveCacheIfChanged,
                interval=None
            )


class WMState:
    """
    スマートメーターから取得した値を保持するクラス


    Examples
    --------
    config = WMConfig(ujson=ujson, uos=uos, logging=logging)
    state = WMState(config=config)
    state.setCurrentWatt(1234)

    Attributes
    ----------
    STATUS_NORMAL : int
        通常状態をあらわす
    STATUS_CAUTION : int
        注意状態をあらわす
    STATUS_WARNING : int
        警告状態をあらわす
        状況が深刻になるにつれて数字が増えるようにする
    CONTINUOUS_ERROR_LIMIT : int
        連続したエラーを許容する回数
        エラー数がここで指定した回数に到達すると例外を発生させる
    """
    STATUS_NORMAL  = 0
    STATUS_CAUTION = 10
    STATUS_WARNING = 20

    CONTINUOUS_ERROR_LIMIT = 10

    def __init__(self, *, config):
        """
        Parameters
        ----------
        config : object
            WMConfigクラスインタンス
        """
        self.config = config
        self._date_parts = None
        self._current_watt = 0
        self._current_status = self.STATUS_NORMAL
        self._is_status_escalated = False
        self._continuous_error_count = 0

    def setTime(self, parts):
        """
        現在の日時を設定する

        Parameters
        ----------
        parts : tuple
            日時の要素で構成されたtuple
            utime.localtime() の戻り値
        """
        self._date_parts = parts

    def getTime(self, format=None):
        """
        設定された日時を文字列として取得する

        Parameters
        ----------
        format : str
            str.format()形式のフォーマット文字列
            以下の名前をフィールド名に使用できる
            year: 年
            mon : 月
            mday: 日
            hour: 時
            min : 分
            sec : 秒
            未指定時のフォーマットは
            {year:d}/{mon:d}/{mday:d} {hour:02d}:{min:02d}

        Returns
        -------
        str | None
            フォーマットされた日時文字列
            日時が未設定の場合はNone
        """
        if self._date_parts is None:
            return None
        if format is None:
            format = "{year:d}/{mon:d}/{mday:d} {hour:02d}:{min:02d}"
        year, mon, mday, hour, min, sec, *_ = self._date_parts
        return format.format(
            year=year,
            mon=mon,
            mday=mday,
            hour=hour,
            min=min,
            sec=sec
        )

    def setCurrentWatt(self, watt):
        """
        現在の消費電力量を設定する

        Parameters
        ----------
        watt : int
            現在の消費電力量(W)
        """
        self._current_watt = watt
        self._updateStatus()
        self._continuous_error_count = 0

    def getCurrentWatt(self):
        """
        設定された消費電力量を取得する

        Returns
        -------
        int
            消費電力量(W)
        """
        return self._current_watt

    def _updateStatus(self):
        """
        現在の状態を更新する

        消費電力量から現在の状態を
        通常: NORMAL
        注意: CAUTION
        警告: WARNING
        のいずれかに設定する
        """
        if self.config.config.wattmeter.warning is not None:
            if self._current_watt >= self.config.config.wattmeter.warning.watt:
                if self._current_status < self.STATUS_WARNING:
                    self._is_status_escalated = True
                self._current_status = self.STATUS_WARNING
                return
        if self.config.config.wattmeter.caution is not None:
            if self._current_watt >= self.config.config.wattmeter.caution.watt:
                if self._current_status < self.STATUS_CAUTION:
                    self._is_status_escalated = True
                self._current_status = self.STATUS_CAUTION
                return
        self._is_status_escalated = False
        self._current_status = self.STATUS_NORMAL

    def isStatusNormal(self):
        """
        現在の状態が"正常"かを判定する

        Returns
        -------
        bool
            正常の場合はTrue
        """
        return self._current_status == self.STATUS_NORMAL

    def isStatusCaution(self):
        """
        現在の状態が"注意"かを判定する

        Returns
        -------
        bool
            注意の場合はTrue
        """
        return self._current_status == self.STATUS_CAUTION

    def isStatusWarning(self):
        """
        現在の状態が"警告"かを判定する

        Returns
        -------
        bool
            警告の場合はTrue
        """
        return self._current_status == self.STATUS_WARNING

    def isStatusEscalated(self):
        """
        直近で状態が悪化したかを判定する

        状態が
        "正常"から"注意"
        "注意"から"警告"
        へと悪化したかを判定する
        1回の状態悪化に対して1度だけTrueを返す

        Returns
        -------
        bool
            直近で状態が悪化していた場合はTrue
        """
        ret = self._is_status_escalated
        self._is_status_escalated = False
        return ret

    def reportError(self, ex):
        """
        エラーの報告を受け取る

        WMStatを利用する側からのエラー(例外)を受け取る
        エラーが設定値を超える回数連続して発生した場合は受け取ったエラーを投げる
        メーターからの値取得が(成功を挟まず)連続して失敗した場合は何らかの問題が発生していると判断して
        処理を停止させるために使用する

        エラーの連続発生数(_continuous_error_count)は値取得が成功した際にリセットする

        Parameters
        ----------
        ex | object
            例外

        Raises
        ------
        Exception
            パラメータで受け取った例外
        """
        self._continuous_error_count += 1
        if self._continuous_error_count < self.CONTINUOUS_ERROR_LIMIT:
            return
        raise ex


class NetworkError(Exception):
    """
    インターネット関連の例外
    """
    pass

class WiSUNError(Exception):
    """
    Wi-SUN関連の例外
    """
    pass

# <<< meter
