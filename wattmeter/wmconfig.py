# wmconfig >>>

class WMConfig:
    """
    設定を扱うクラス

    設定の読み込み, 設定キャッシュの読み込み/書き込みを行うクラス

    設定ファイルは利用者が作成したファイルで読み込みのみ

    設定キャッシュファイルは動作の過程で生成される値を保存するファイル
    アプリケーションが生成し更新する

    Example
    -------
    import ujson, uos
    from wmlogging import Logger as logging

    config = WMConfig(ujson=ujson, uos=uos, logging=logging)
    config.load()

    Attributes
    ----------
    CONFIG_FILE_PATH : str
        設定ファイルのファイルパス
    CACHE_FILE_PATH : str
        設定キャッシュファイルのファイルパス
    DEFAULT_CONFIG : dict
        設定のデフォルト値
    DEFAULT_CACHE : dict
        キャッシュのデフォルト値
    """
    CONFIG_FILE_PATH = "/flash/wmconfig.json"
    CACHE_FILE_PATH = "/flash/wmcache.json"

    DEFAULT_CONFIG = {
        "network": {
            "wifi": None,
            "ntp": {
                "server": "ntp.nict.jp",
                "timezone": 9
            }
        },
        "b_route": None,
        "wattmeter": {
            "max": {
                "watt": 5000
            },
            "warning": None,
            "caution": None,
            "update_interval": 30,
            "beep_volume": 3,
            "auto_reboot": True,
            "sync_cache": False,
        },
        "display": {
            "brightness": 50,
            "sleep": None
        }
    }
    DEFAULT_CACHE = {
        "channel": None,
        "pan_id": None,
        "mac_addr": None,
        "factor": None,
        "unit": None,
        "significant_figures": None,
        "display_flip": False,
        "face_id": 0
    }

    def __init__(self, *, ujson, uos, logging):
        """
        Parameters
        ----------
        ujson : object
            ujsonモジュール
        uos : object
            uosモジュール
        logging : object
            loggingモジュール
        """
        self._ujson = ujson
        self._uos = uos
        self._logging = logging
        self._config = None
        self._cache = None
        self._cache_saved = None

    def _isFileExists(self, path):
        """
        指定されたパスにファイルが存在するかを調べる

        Parameters
        ----------
        path : str
            ファイルパス

        Returns
        -------
        bool
            存在する場合はTrue
        """
        prefix = ""
        if path.startswith("/"):
            prefix = "/"
        segments = path.lstrip("/").split("/")
        dir = prefix + "/".join(segments[0:-1])
        basename = segments[-1]
        for entry in self._uos.ilistdir(dir):
            if entry[0] == basename and entry[1] == 0x8000:
                """
                0x4000 (16384) ディレクトリ
                0x8000 (32768) 通常ファイル
                """
                return True
        return False

    def _deepCopy(self, obj):
        """
        オブジェクトをdeep copyする

        Parameters
        ----------
        obj : object
            コピー元のオブジェクト

        Returns
        -------
        object
            コピーされたオブジェクト
        """
        ujson = self._ujson
        return ujson.loads(ujson.dumps(obj))

    def _recursiveMerge(self, base, other):
        """
        dictを再帰的にマージする

        dict.update()を再帰的に実行する
        設定をデフォルトとマージするために使用する

        Parameters
        ----------
        base : dict
            元になるdict
        other : dict
            上書きするdict

        Returns
        -------
        dict
            マージされたdict
        """
        if not isinstance(base, dict):
            return self._deepCopy(other)
        base_copy = base.copy()
        for k, v in other.items():
            if isinstance(v, dict) and k in base_copy:
                base_copy[k] = self._recursiveMerge(base_copy[k], v)
            else:
                base_copy[k] = v
        return base_copy

    def _loadConfig(self):
        """
        設定ファイルを読み込む
        """
        with open(self.CONFIG_FILE_PATH, "r") as f:
            config = self._ujson.load(f)
            self._config = AttrDict(self._recursiveMerge(self.DEFAULT_CONFIG, config))
            self._logging.debug(self._config)

    def _loadCache(self):
        """
        設定キャッシュファイルを読み込む
        """
        if not self._isFileExists(self.CACHE_FILE_PATH):
            self._logging.info("cache miss: " + self.CACHE_FILE_PATH)
            self._cache = AttrDict(self.DEFAULT_CACHE)
            self._cache_saved = self._deepCopy(self._cache.getDict())
            return
        with open(self.CACHE_FILE_PATH, "r") as f:
            logger = self._logging
            logger.info("cache hit: " + self.CACHE_FILE_PATH)
            cache = self._ujson.load(f)
            base = self._deepCopy(self.DEFAULT_CACHE)
            base.update(cache)
            logger.debug(base)
            self._cache = AttrDict(base)
            self._cache_saved = self._deepCopy(self._cache.getDict())

    def _validateConfig(self):
        """
        設定(ファイル)の内容を検証する

        読み込まれた設定の内容を検証する
        * 必須項目が設定されているか
        * 値の形式が正しいか
        * 矛盾した設定になっていないか
        """
        config = self._config
        # wifi はNone又はssidとpasswordの値が存在しなければならない
        if config.wifi is not None:
            if config.wifi.ssid is None or config.wifi.password is None:
                raise InvalidConfigError("Both wifi.ssid and wifi.password must be present.")

        # b_route はidとpasswordの値が存在しなければならない
        if config.b_route is None:
            raise InvalidConfigError("b_route must be present.")
        if config.b_route.id is None or config.b_route.password is None:
            raise InvalidConfigError("Both b_route.id and b_route.password must be present.")
        # b_route.idの形式(文字数のみ)
        if not isinstance(config.b_route.id, str):
            raise InvalidConfigError("b_route.id must be a string.")
        if len(config.b_route.id) != 32:
            raise InvalidConfigError("b_route.id must be 32 characters.")
        # b_route.passwordの形式
        if not isinstance(config.b_route.password, str):
            raise InvalidConfigError("b_route.password must be a string.")

        # wattmeter.max.wattは必須で値は数値1000-9999の範囲
        if config.wattmeter is None or config.wattmeter.max is None or config.wattmeter.max.watt is None:
            raise InvalidConfigError("wattmeter.max.watt must be present.")
        if not isinstance(config.wattmeter.max.watt, int):
            raise InvalidConfigError("wattmeter.max.watt must be an integer.")
        if config.wattmeter.max.watt < 1000 or config.wattmeter.max.watt > 9999:
            raise InvalidConfigError("wattmeter.max.watt must be in the range of 1000 to 9999.")

        # wattmeter.warning.wattは数値でmaxより小さい
        if config.wattmeter.warning is not None:
            if not isinstance(config.wattmeter.warning.watt, int):
                raise InvalidConfigError("wattmeter.warning.watt must be an integer.")
            if config.wattmeter.warning.watt < 1:
                raise InvalidConfigError("wattmeter.warning.watt must be greater than 0.")
            if config.wattmeter.warning.watt >= config.wattmeter.max.watt:
                raise InvalidConfigError("wattmeter.warning.watt must be less than wattmeter.max.watt.")

        # wattmeter.caution.wattは数値でwarning/maxより小さい
        if config.wattmeter.caution is not None:
            if not isinstance(config.wattmeter.caution.watt, int):
                raise InvalidConfigError("wattmeter.caution.watt must be an integer.")
            if config.wattmeter.caution.watt < 1:
                raise InvalidConfigError("wattmeter.caution.watt must be greater than 0.")
            if config.wattmeter.warning is not None:
                if config.wattmeter.caution.watt >= config.wattmeter.warning.watt:
                    raise InvalidConfigError("wattmeter.caution.watt must be less than wattmeter.warning.watt.")
            else:
                if config.wattmeter.caution.watt >= config.wattmeter.max.watt:
                    raise InvalidConfigError("wattmeter.caution.watt must be less than wattmeter.max.watt.")

        if config.display is not None:
            # display.brightnessは数値で0-100の範囲(axp.setLcdBrightness())
            if config.display.brightness is not None:
                if not isinstance(config.display.brightness, int):
                    raise InvalidConfigError("display.brightness must be an integer.")
                if config.display.brightness < 0 or config.display.brightness > 100:
                    raise InvalidConfigError("display.brightness must be in the range of 0 to 100.")

            if config.display.sleep is not None:
                # display.sleep はNone又はstartとendの値が存在しなければならない
                if config.display.sleep.start is None or config.display.sleep.end is None:
                    raise InvalidConfigError("Both display.sleep.start and display.sleep.end must be present.")

                # display.sleep startとendの値の形式("01:23"形式)
                if not isinstance(config.display.sleep.start, str):
                    raise InvalidConfigError("Invalid display.sleep.start format.")
                segments = config.display.sleep.start.split(":")
                if len(segments) != 2:
                    raise InvalidConfigError("Invalid display.sleep.start format.")
                if not segments[0].isdigit() or not segments[1].isdigit():
                    raise InvalidConfigError("Invalid display.sleep.start format.")
                if int(segments[0]) > 23 or int(segments[1]) > 59:
                    raise InvalidConfigError("Invalid display.sleep.start format.")

                if not isinstance(config.display.sleep.end, str):
                    raise InvalidConfigError("Invalid display.sleep.end format.")
                segments = config.display.sleep.end.split(":")
                if len(segments) != 2:
                    raise InvalidConfigError("Invalid display.sleep.end format.")
                if not segments[0].isdigit() or not segments[1].isdigit():
                    raise InvalidConfigError("Invalid display.sleep.end format.")
                if int(segments[0]) > 23 or int(segments[1]) > 59:
                    raise InvalidConfigError("Invalid display.sleep.end format.")

                # display.sleep.start != display.sleep.end (6:00と06:00は通過してしまう)
                if config.display.sleep.start == config.display.sleep.end:
                    raise InvalidConfigError("display.sleep.start and display.sleep.end must not be the same.")

    def _calcSleepTime(self):
        """
        スリープ時間の計算を行う

        display.sleep が設定されていた場合に時間の計算を行い設定する
        display.sleep.start_time に start の時間がその日の00:00から何秒経過後かを設定
        display.sleep.duration に start から end の期間が何秒間かを設定
        end が start より前の時刻になる場合は翌日の end の時刻までの期間
        """
        config = self._config
        if config.display.sleep is None:
            return
        h, m = config.display.sleep.start.split(":")
        start_hour = int(h)
        start_min = int(m)
        start_time = start_hour * 3600 + start_min * 60
        config.display.sleep.start_time = start_time
        h, m = config.display.sleep.end.split(":")
        end_hour = int(h)
        end_min = int(m)
        end_time = end_hour * 3600 + end_min * 60
        if end_time < start_time:
            end_time += 86400
        config.display.sleep.duration = end_time - start_time

    @property
    def config(self):
        return self._config

    @property
    def cache(self):
        return self._cache

    def load(self):
        """
        設定ファイル/設定キャッシュファイルから設定を読み込む
        """
        self._loadConfig()
        self._validateConfig()
        self._calcSleepTime()
        self._loadCache()

    def saveCache(self):
        """
        設定キャッシュファイルに現在の設定を保存する

        設定キャッシュファイルを直接開きサイズを0にした後に書き込む
        一時ファイルに書き込んだ後renameでファイルを置換する方法(ファイルシステムによってはアトミックな書き換えとなる)ではない
        """
        cache = self._cache
        to_save_obj = {
            "channel"            : cache.channel,
            "pan_id"             : cache.pan_id,
            "mac_addr"           : cache.mac_addr,
            "factor"             : cache.factor,
            "unit"               : cache.unit,
            "significant_figures": cache.significant_figures,
            "display_flip"       : cache.display_flip,
            "face_id"            : cache.face_id
        }
        with open(self.CACHE_FILE_PATH, "w") as f:
            self._ujson.dump(to_save_obj, f)
            self._logging.info("cache saved")
        self._cache_saved = to_save_obj

    def saveCacheIfChanged(self):
        """
        値に変更があった場合は設定キャッシュファイルに設定を保存する

        設定キャッシュファイルから読み込んだ値に変更があった場合は上書きする
        値に変更がない場合は書き込みを行わない
        書き込み回数に上限のあるフラッシュメモリへの書き込み回数を減らすための処置

        Returns
        -------
        bool
            実際に保存された場合はTrue
            保存されなかった(必要なかった)場合はFalse
        """
        if self._cache == self._cache_saved:
            self._logging.info("skip cache saving")
            return False
        self.saveCache()
        return True

    def removeCache(self):
        """
        設定キャッシュファイルを削除する

        値が無効になっているなどの場合にキャッシュファイルは削除する
        ファイル削除後もcacheの値はそのまま
        """
        if self._isFileExists(self.CACHE_FILE_PATH):
            self._uos.remove(self.CACHE_FILE_PATH)

class AttrDict:
    """
    .形式で属性にアクセスできるクラス

    collections.namedtupleに似た.形式で属性の読み書きができる
    RubyのOpenStructに似たクラス
    初期化時点で定義されていない属性にはアクセスできない(読み込みではNoneが返る)

    > config["network"]["wifi"]["ssid"]
    このような形式ではなく
    > config.network.wifi.ssid
    このように"."で区切る形式で属性にアクセスできる
    """
    def __init__(self, kv):
        """
        Parameters
        ----------
        kv : dict
            内部で使用するデータ
        """
        for k, v in kv.items():
            if isinstance(v, dict):
                setattr(self, k, self.__class__(v))
            else:
                setattr(self, k, v)

    def __getattr__(self, _):
        """
        見つからない属性の取得時の処理

        setattrで追加されていない属性の取得時の処理
        エラーは発生させずNoneを返す

        Returns
        -------
        None
        """
        return None

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        """
        インスタンスと他の値を比較する

        同じインスタンスの場合は内部のdict同士を比較する
        dictとの比較は内部のdictと渡されたdictを比較する

        Parameters
        ----------
        other : AttrDict | dict
            比較対象

        Returns
        -------
        bool
            一致する場合はTrue
        """
        if isinstance(other, dict):
            return self.getDict() == other
        elif isinstance(other, self.__class__):
            return self.getDict() == other.getDict()
        return NotImplemented

    def getDict(self):
        """
        値が設定されている属性をdictで取得する

        Returns
        -------
        dict
            値が設定されている属性のdict
        """
        result = {}
        for k, v in self.__dict__.items():
            if isinstance(v, self.__class__):
                result[k] = v.getDict()
            else:
                result[k] = v
        return result

class InvalidConfigError(Exception):
    """
    設定内容が正しくない場合の例外
    """
    pass

# <<< wmconfig
