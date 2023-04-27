# wmlogging >>>

class Logger:
    """
    ログ出力を行うクラス

    Pythonのloggingモジュールに似た機能を提供するクラス
    loggingモジュールから可能な限り機能を減らした実装
    MicroPythonで組み込みのloggingが使えないなど色々な事情があり車輪の再発明が行われている

    Examples
    --------
    import utime

    Logger.basicConfig(
        utime=utime,
        level=Logger.INFO
    )
    Logger.info("info message")
    Logger.log(Logger.WARNING, "warning message")
    """

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10

    _LEVEL_TO_NAME = {
        CRITICAL: "CRITICAL",
        ERROR   : "ERROR",
        WARNING : "WARNING",
        INFO    : "INFO",
        DEBUG   : "DEBUG",
    }

    _output_level = WARNING

    _output_func = print

    _time_module = None

    def __init__(self):
        raise Exception("Do not create the instance.")

    @classmethod
    def _getDateTimeString(cls):
        """
        ログに出力する日時文字列を取得する

        "[YYYY-MM-DD hh:mm:ss] " 形式の日時文字列を取得する
        _time_moduleがNoneの場合は空文字が返る

        Returns
        -------
        str
            日時文字列
        """
        if cls._time_module is None:
            return ""
        return "[{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}] ".format(*cls._time_module.localtime())

    @classmethod
    def reset(cls):
        """
        ログの設定をデフォルトにリセットする

        basicConfig()で行った設定をリセットする
        """
        cls._output_level = cls.WARNING
        cls._output_func = print
        cls._time_module = None

    @classmethod
    def basicConfig(cls, **kwards):
        """
        ログに関する設定を行う

        Parameters
        ----------
        kwards : dict
            level : int
                出力するログレベル
                指定したレベルより高いレベルのログのみ出力
                デフォルトはWARNING
            utime : module
                utimeモジュール
                日付の出力に使用する
            output_func : function
                ログ出力に使用する関数
                output_func(message) の形式で呼び出される
                指定しない場合はprint
        """
        if kwards.get("level", None) is not None:
            cls._output_level = kwards.get("level")
        cls._time_module = kwards.get("utime", None)
        if kwards.get("output_func", None) is not None:
            cls._output_func = kwards.get("output_func")

    @classmethod
    def log(cls, level, message):
        if level < cls._output_level:
            return
        dateStr = cls._getDateTimeString()
        levelName = cls._LEVEL_TO_NAME.get(level, "UNKNOWN")
        cls._output_func(dateStr + levelName + ": " + str(message))

    @classmethod
    def debug(cls, message):
        cls.log(cls.DEBUG, message)

    @classmethod
    def info(cls, message):
        cls.log(cls.INFO, message)

    @classmethod
    def warning(cls, message):
        cls.log(cls.WARNING, message)

    @classmethod
    def error(cls, message):
        cls.log(cls.ERROR, message)

    @classmethod
    def critical(cls, message):
        cls.log(cls.CRITICAL, message)

    @classmethod
    def exception(cls, ex):
        cls.log(cls.ERROR, "<" + ex.__class__.__name__ + "> " + str(ex))

# <<< wmlogging
