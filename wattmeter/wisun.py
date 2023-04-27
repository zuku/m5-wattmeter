# wisun >>>

class BP35A1Client:
    """
    BP35A1のクライアントクラス

    Wi-SUN対応無線モジュールROHM BP35A1をWi-SUN HATキットを経由して扱うためのクラス

    Examples
    --------
    from machine import UART
    import utime
    from wmlogging import Logger as logging

    b_route_id = "00000000000000000000000000000000"
    b_route_password = "XXXXXXXXXXXX"

    client = BP35A1Client(uart=UART, utime=utime, logging=logging)

    client.isDeviceAvailable()
    client.execEchoBack(False)
    client.execSetAsciiMode()
    client.execSetPwd(b_route_password)
    client.execSetRbId(b_route_id)

    scan_result = client.execScan()
    client.execSetChannel(scan_result["Channel"])
    client.execSetPanId(scan_result["Pan ID"])
    ip_address = client.execConvertAddress(scan_result["Addr"])
    client.execJoin(ip_address)

    client.execGetStatus()
    factor = client.execGetFactor()
    unit = client.execGetIntegralPowerConsumptionUnit()
    client.setPowerConsumptionCalcParams(factor=factor, unit=unit)

    client.execGetCurrentPowerConsumption()

    Attributes
    ----------
    DEVICE_ID : int
        デバイスID
    DEVICE_TX : int
        Wi-SUN HATキットのTXピン番号
    DEVICE_RX : int
        Wi-SUN HATキットのRXピン番号
    DEVICE_BAUDRATE : int
        BP35A1との通信に使用するボーレート
    DEVICE_BITS : 7, 8, 9
        BP35A1との通信での1文字あたりのビット数
    DEVICE_PARITY : None | 0, 1
        BP35A1との通信でのパリティビット
    DEVICE_STOP : 1, 2
        BP35A1との通信でのストップビット
    DEVICE_TIMEOUT_MS : int
        BP35A1との通信で最初の文字を待つ時間(ミリ秒)
    DEFAULT_READ_RETRY : int
        BP35A1からデータを受信する際のデフォルト再試行回数
    DEFAULT_READ_WAIT_TIME_MS : int
        BP35A1にコマンドを送信してから受信するまでに待機するデフォルトの時間(ミリ秒)
    DEFAULT_RETRY_WAIT_TIME_MS : int
        BP35A1からのデータを受信をリトライする際のデフォルトの待機時間(ミリ秒)
    MAX_LOOP_COUNT : int
        BP35A1からのデータ受信がループになった場合の最大繰り返し回数
        通常は発生しないが異常時に無限ループにならないための対策
    SCAN_READ_WAIT_TIME_MS : int
        SKSCANコマンド実行時のコマンド実行後受信待ち時間(ミリ秒)
    SCAN_RETRY_WAIT_TIME_MS : int
        SKSCANコマンド実行時のリトライ待機時間(ミリ秒)
        通常のコマンドより応答に時間がかかる
    SCAN_RETRY_COUNT : int
        SKSCANコマンド実行時のリトライ回数
    JOIN_RETRY_WAIT_TIME_MS : int
        SKJOINコマンド実行時のリトライ待機時間(ミリ秒)
        通常のコマンドより応答に時間がかかる
    JOIN_RETRY_COUNT : int
        SKJOINコマンド実行時のリトライ回数
    SENDTO_READ_WAIT_TIME_MS : int
        SKSENDTOコマンド実行時のコマンド実行後受信待ち時間(ミリ秒)
    SENDTO_RETRY_WAIT_TIME_MS : int
        SKSENDTOコマンド実行時のリトライ待機時間(ミリ秒)
    SENDTO_RETRY_COUNT : int
        SKSENDTOコマンド実行時のリトライ回数
    CRLF : str
        改行文字
        コマンドを区切る文字
    """
    DEVICE_ID = 1
    DEVICE_TX = 0
    DEVICE_RX = 26
    DEVICE_BAUDRATE = 115200
    DEVICE_BITS = 8
    DEVICE_PARITY = None
    DEVICE_STOP = 1
    DEVICE_TIMEOUT_MS = 2000

    DEFAULT_READ_RETRY = 5
    DEFAULT_READ_WAIT_TIME_MS = 500
    DEFAULT_RETRY_WAIT_TIME_MS = 100
    MAX_LOOP_COUNT = 200

    SCAN_READ_WAIT_TIME_MS = 5000
    SCAN_RETRY_WAIT_TIME_MS = 3000
    SCAN_RETRY_COUNT = 8

    JOIN_RETRY_WAIT_TIME_MS = 1000
    JOIN_RETRY_COUNT = 30

    SENDTO_READ_WAIT_TIME_MS = 500
    SENDTO_RETRY_WAIT_TIME_MS = 500
    SENDTO_RETRY_COUNT = 20

    CRLF = "\r\n"

    def __init__(self, *, uart, utime, logging):
        """
        Parameters
        ----------
        uart : object
            machine.UARTクラス
        utime : object
            utimeモジュール
            内部的な通信の待機(sleep)に使用する
        logging : object
            loggingモジュール
        """
        self._utime = utime
        self._client = self._createClient(uart)
        self._logging = logging
        self._tid = 0
        self._ip_address = None
        self._factor = 1
        self._unit = 1

    def _createClient(self, uart):
        """
        BP35A1との通信バスを作成して初期化する

        Parameters
        ----------
        uart : object
            machine.UARTクラス

        Returns
        -------
        object
            uartオブジェクト
        """
        client = uart(__class__.DEVICE_ID, tx=__class__.DEVICE_TX, rx=__class__.DEVICE_RX)
        client.init(
            __class__.DEVICE_BAUDRATE,
            bits    = __class__.DEVICE_BITS,
            parity  = __class__.DEVICE_PARITY,
            stop    = __class__.DEVICE_STOP,
            timeout = __class__.DEVICE_TIMEOUT_MS
        )
        return client

    def _writeAndReadline(self, command, break_words = None, *, max_retry = None, pre_wait = None, retry_wait = None, auto_crlf = True):
        """
        BP35A1にコマンドを送信(write)して結果を1行ずつ受信(readline)する

        Parameters
        ----------
        command : str | bytes
            送信するコマンド文字列
            auto_crlf = True の場合末尾に改行(CRLF)が付加される
        break_words : str | [str, str]
            指定した文字列が受信した行の中に含まれていたら処理を終了する
            リストを渡した場合はリスト内のいずれかの文字列が行の中に含まれていたら処理を終了する
            Noneの場合は繰り返しの上限回数まで処理を続ける
        max_retry : int
            受信処理を繰り返す最大の回数(1を指定した場合は受信処理は最大2回行われる)
            Noneの場合は DEFAULT_READ_RETRY 回数繰り返す
        pre_wait : int
            コマンドを送信してから受信処理を行う前に待機する時間(ミリ秒)
            Noneの場合は DEFAULT_READ_WAIT_TIME_MS 待機する
        retry_wait : int
            受信処理を繰り返す際に待機する時間(ミリ秒)
            Noneの場合は DEFAULT_RETRY_WAIT_TIME_MS 待機する
        auto_crlf : bool
            Trueの場合渡されたコマンドの末尾に改行が付加される

        Returns
        -------
        list [str, str]
            受信した各行のリスト
            末尾の改行文字は取り除かれている

        Raises
        -------
        ReadTimeoutError
            規定の処理時間(回数)内で指定されたbreak_wordsが見つからなかった場合に発生する
        """
        client = self._client
        utime = self._utime
        class_name = self.__class__.__name__
        logger = self._logging
        if max_retry is None:
            max_retry = self.DEFAULT_READ_RETRY
        if pre_wait is None:
            pre_wait = self.DEFAULT_READ_WAIT_TIME_MS
        if retry_wait is None:
            retry_wait = self.DEFAULT_RETRY_WAIT_TIME_MS

        command_head = str(command).split(" ", 1)[0]
        if command_head.startswith("b'"):
            command_head = command_head[2:]
        logger.info(class_name + " write command [" + command_head + "]")
        logger.debug(command)
        if auto_crlf:
            client.write(command + self.CRLF)
        else:
            client.write(command)
        max_loop_count = self.MAX_LOOP_COUNT
        response_lines = []
        searches = []
        if type(break_words) is str:
            searches.append(break_words)
        elif type(break_words) is list or type(break_words) is tuple:
            searches = list(break_words)
        logger.debug(class_name + " search words " + str(searches))

        waits = [pre_wait]
        waits += [retry_wait] * max_retry
        for wait in waits:
            utime.sleep_ms(wait)
            loop_count = 0
            while client.any() > 0 and loop_count < max_loop_count:
                line = client.readline()
                if line is not None:
                    if type(line) is bytes:
                        line = line.decode()
                    line = line.rstrip()
                    response_lines.append(line)
                    for search_str in searches:
                        if search_str in line:
                            logger.debug(response_lines)
                            return response_lines
                loop_count += 1
                logger.debug(class_name + " waiting response. count = " + str(loop_count))
            if loop_count >= max_loop_count:
                raise ReadTimeoutError("Infinite loop detected. (" + command_head + ")")
        if break_words is not None:
            raise ReadTimeoutError("Read timed out. (" + command_head + ")")

        return response_lines

    def _sendUDPData(self, ip_address, data, break_words = None):
        """
        指定した宛先にUDPでデータを送信する

        SKSENDTOコマンドを使用して指定した宛先にUDPでデータを送信する

        UDPハンドルは 1 固定
        宛先ポート番号は 0x0E1A 固定
        暗号化オプションは 1 (常に暗号化)固定

        Parameters
        ----------
        ip_address : str
            宛先のIPv6アドレス
        data : bytes
            送信するデータ
        break_words : str | [str, str]
            受信待ち処理終了のキーワード

        Returns
        -------
        list [str, str]
            受信した各行のリスト
        """
        if ip_address is None:
            raise UndefinedAddressError("IPv6 address must not be None.")
        command = "SKSENDTO 1 {ip_address} {port:04X} {sec:d} {data_len:04X} ".format(
            ip_address = ip_address,
            port = 0x0E1A,
            sec = 1,
            data_len = len(data)
        )
        response = self._writeAndReadline(
            command.encode("utf-8") + data,
            break_words = break_words,
            max_retry   = self.SENDTO_RETRY_COUNT,
            pre_wait    = self.SENDTO_READ_WAIT_TIME_MS,
            retry_wait  = self.SENDTO_RETRY_WAIT_TIME_MS,
            auto_crlf   = False
        )
        return response

    def _extractUDPData(self, event):
        """
        UDP受信通知から受信データを取り出す

        ERXUDPイベントによって通知された内容をから受信データ部分を取り出す

        Parameters
        ----------
        event : str
            ERXUDPイベントの内容(改行を含まない)

        Returns
        -------
        str
            受信データ
        """
        _, _, _, _, _, _, _, _, response_data = event.split(" ")
        return response_data

    def _findFrameFromResponseEvents(self, events, sent_frame):
        """
        送信したフレームに対応する応答を探して解析して返す

        SKSENDTOコマンドの送信後に受信したERXUDPイベント(複数)の中から送信したECHONET Liteフレームに対応する
        応答を見つけてフレームデータを解析して返す
        対応するフレームが複数見つかった場合は最初に受信したフレームを返す

        Parameters
        ----------
        events : list [str, str]
            受信した内容文字列の配列
            ASCIIモードでの応答にのみ対応
        sent_frame : bytes
            送信したフレームデータ
            フレームデータのTID, EPCが一致する受信フレームを探す

        Returns
        -------
        dict | None
            受信したECHONET Liteフレームデータを解析したdict
            対応する応答を見つけられなかった場合はNone
        """
        tid = int.from_bytes(sent_frame[2:4], "big")
        epc = int.from_bytes(sent_frame[12:13], "big")
        for event in events:
            if not event.startswith("ERXUDP "):
                continue
            frame = self._parseEchonetLiteFrame(self._extractUDPData(event))
            if frame["TID"] == tid and frame["EPC"] == epc:
                return frame
        return None

    def _createEchonetLiteFrame(self, *, epc, tid = 0x01, esv = 0x62, edt = None):
        """
        ECHONET Liteフレームデータを生成する

        ECHONET Lite ver1.14の仕様をもとにフレームの電文を生成する

        この関数で生成されるフレームには以下の規定がある
        * ECHONET Liteオブジェクトは固定
          * 送信元
            * コントローラクラス
              * クラスグループコード: 0x05
              * クラスコード: 0xFF
              * インスタンスコード: 0x01 (0x01-0x7F の範囲で変更可能)
          * 相手先
            * 低圧スマート電力量メータクラス
              * クラスグループコード: 0x02
              * クラスコード: 0x88
              * インスタンスコード: 0x01 (0x01-0x7F の範囲で変更可能)
        * OPCは1固定

        Parameters
        ----------
        epc : int
            ECHONET Liteプロパティ
        tid : int
            トランザクションID
        esv : int
            対象プロパティに対する操作
            0x62 Get 読み出し要求 (デフォルト)
            0x61 SetC 書き込み要求
        edt : bytes
            プロパティ値データ

        Returns
        -------
        bytes
            ECHONET Liteフレーム
        """
        ehd1 = 0x10  # ECHONET Lite規格
        ehd2 = 0x81  # 形式1

        seoj = 0x05FF01  # 送信元ECHONET Liteオブジェクト
        deoj = 0x028801  # 相手先ECHONET Liteオブジェクト
        opc  = 0x01  # 要求数:1
        pdc  = 0x00  # EDTバイト数
        if edt is not None:
            pdc = len(edt)

        frame = (
            ehd1.to_bytes(1, 'big') +
            ehd2.to_bytes(1, 'big') +
            tid.to_bytes(2, 'big') +
            seoj.to_bytes(3, 'big') +
            deoj.to_bytes(3, 'big') +
            esv.to_bytes(1, 'big') +
            opc.to_bytes(1, 'big') +
            epc.to_bytes(1, 'big') +
            pdc.to_bytes(1, 'big')
        )
        if edt is not None:
            frame += edt
        return frame

    def _createExpectedEchonetLiteResponseLeadingFrame(self, frame):
        """
        要求のECHONET Liteフレームから期待する応答のフレームの先頭部分を生成する

        要求した内容に対する応答であるかを判別するために使用する
        実質TIDが一致するかどうか

        EHD1からDEOJまでの値を使用する
        ESVは要求不可応答の場合もあるため要求から応答の値が一意に決まらない

        EHD1, EHD2, TIDは要求と同一
        SEOJ, DEOJは場所を入れ替える

        Parameters
        ----------
        frame : bytes
            要求のECHONET Liteフレーム

        Returns
        -------
        str
            期待する応答のECHONET Liteフレーム文字列
            16進数表記(大文字)
        """
        expected_frame_bytes = frame[0:4] + frame[7:10] + frame[4:7]
        expected_frame = ""
        for b in expected_frame_bytes:
            expected_frame += "%02X" % b
        return expected_frame.upper()

    def _createBreakWordsFromFrame(self, frame):
        """
        ECHONET Liteフレームからレスポンスの検索条件を生成する

        UDPデータを送信する _writeAndReadline() のbreak_wordsパラメータとして使用するリストを生成する

        Parameters
        ----------
        frame : bytes
            要求のECHONET Liteフレーム

        Returns
        -------
        tuple : (str, str)
            break_wordsで使用する文字列のtuple
            16進数表記の大文字と小文字
        """
        break_word = " " + self._createExpectedEchonetLiteResponseLeadingFrame(frame)
        return (break_word, break_word.lower())

    def _parseEchonetLiteFrame(self, frame):
        """
        ECHONET Liteフレームデータを解析して要素として取り出す

        この関数では以下の条件を満たすフレームのみ解析できる
        * OPCが1

        Parameters
        ----------
        frame : str
            フレームデータの16進数表記文字列
            バイト列(例: b'\x00\xFF')ではない

        Returns
        -------
        dict
            フレームデータの各要素を格納したdict
            以下の要素が含まれる
            EHD1 : int
            EHD2 : int
            TID : int
            SEOJ : int
            DEOJ : int
            ESV : int
            OPC : int
            EPC : int
            PDC : int
            EDT : str
                EDTはintではなく16進数表記の文字列
        """
        if len(frame) < 28:
            raise ValueError("Frame data too short.")
        data = {}
        data["EHD1"] = int(frame[0:2], 16)
        data["EHD2"] = int(frame[2:4], 16)
        data["TID"]  = int(frame[4:8], 16)
        data["SEOJ"] = int(frame[8:14], 16)
        data["DEOJ"] = int(frame[14:20], 16)
        data["ESV"]  = int(frame[20:22], 16)
        data["OPC"]  = int(frame[22:24], 16)
        data["EPC"]  = int(frame[24:26], 16)
        data["PDC"]  = int(frame[26:28], 16)
        if data["PDC"] > 0:
            data["EDT"]  = frame[28:]
        else:
            data["EDT"] = None
        return data

    def _requestEDTAsIntFromSmartMeter(self, ip_address, epc):
        """
        スマートメータに問い合わせを行い応答のEDTをintとして取得する

        Parameters
        ----------
        ip_address : str
            問い合わせ先のIPv6アドレス
        epc : int
            問い合わせるプロパティ

        Returns
        -------
        int | None
            EDTの整数表現
            問い合わせに適切な応答がなかった場合はNone
        """
        frame = self._createEchonetLiteFrame(epc=epc, tid=self._nextTransactionId())
        search_frames = self._createBreakWordsFromFrame(frame)
        response_frame = self._findFrameFromResponseEvents(self._sendUDPData(ip_address, frame, search_frames), frame)
        if response_frame is None:
            return None
        if response_frame["EDT"] is None:
            return None
        return int(response_frame["EDT"], 16)

    def _convertUnsignedToSigned(self, digit, bit_size):
        """
        符号なし整数を符号付き整数に変換する

        Parameters
        ----------
        digit : int
            変換する符号なし整数
        bit_size : int
            整数のビット長

        Returns
        -------
        int
            変換された符号付き整数
        """
        return digit - (digit >> (bit_size - 1) << bit_size)

    def _nextTransactionId(self):
        """
        次のTransaction IDを返す

        ECHONET Liteフレームで使用するTIDの値を返す

        Returns
        -------
        int
            次のTransaction ID
            1-65535
        """
        tid = self._tid
        if tid >= 0xFFFF:
            tid = 0
        tid += 1
        self._tid = tid
        return tid

    def clearBuffer(self):
        """
        デバイスのバッファ内に残ったデータをクリアする
        """
        self._writeAndReadline("", max_retry=1, pre_wait=1000, retry_wait=1000)

    def isDeviceAvailable(self):
        """
        デバイスが使用可能かを判定する

        BP35A1が接続されていて使用可能かを判定する

        Returns
        -------
        bool
            使用可能であればTrue
        """
        try:
            self.execGetInfo()
        except ReadTimeoutError:
            return False
        return True

    def execGetInfo(self):
        """
        デバイスの設定情報を取得する

        SKINFOコマンドを使用してデバイスの設定情報を取得する

        Returns
        -------
        dict
            デバイスの設定情報を格納したdict
            ip_address : str
                IPv6アドレス
            mac_address : str
                MACアドレス
            channel : str
                チャンネル(16進数表記)
            pan_id : str
                PAN ID(16進数表記)

        Raises
        -------
        UnexpectedResponseError
            デバイスからの応答にEINFOが含まれていなかった場合に発生する
        """
        response = self._writeAndReadline("SKINFO", "OK")
        for line in response:
            if line.startswith("EINFO "):
                _, ip_address, mac_address, channel, pan_id, _ = line.split(" ", 6)
                return {
                    "ip_address" : ip_address,
                    "mac_address": mac_address,
                    "channel"    : channel,
                    "pan_id"     : pan_id,
                }
        raise UnexpectedResponseError("SKINFO returns unexpected response.")

    def execEchoBack(self, flag):
        """
        BP35A1のエコーバックフラグを設定する

        SKSREGコマンドを使用してエコーバックフラグ(SFE)をあり(1)またはなし(0)に設定する

        Parameters
        ----------
        flag : bool
            Trueの場合ありに設定する
            Falseの場合なしに設定する
        """
        val = "1" if flag else "0"
        self._writeAndReadline("SKSREG SFE " + val, "OK")

    def execSetAsciiMode(self):
        """
        データ部の表示形式をASCII文字に設定する

        WOPT 01を実行してデータ部の表示形式をASCII文字に設定する
        WOPTでの設定は本体のFLASHメモリに保存される
        FLASHメモリには書き込み回数の制限(10,000回以下)があるため設定は必要な場合のみ行う
        ROPTを実行して現在の設定が00(バイナリ)の場合のみWOPTによる設定を行う

        Returns
        -------
        bool
            WOPTを実行し設定変更が行われた場合はTrue
        """
        response = self._writeAndReadline("ROPT", "OK")
        if response[-1].startswith("OK 00"):
            self._writeAndReadline("WOPT 01", "OK")
            return True
        return False

    def execTerminateSession(self):
        """
        PANAセッションを終了する

        SKTERMを実行して現在のPANAセッションの終了を要請する
        セッションが開始していなかった場合は失敗するが開始していないので終了している

        Returns
        -------
        bool
            セッションが正常に終了した場合はTrue
            セッションが存在しないなど正しく修了しなかった場合はFalse
        """
        self._ip_address = None
        response = self._writeAndReadline("SKTERM", ["OK", "FAIL ER10"])
        if response[-1].startswith("OK"):
            return True
        return False

    def execSetPwd(self, pwd):
        """
        パスワードを登録する

        SKSETPWDを実行してパスワードを登録する
        SKSETPWD+<LEN>+<PWD>
        <LEN>は<PWD>の長さの16進数表記なので常に C (12)

        Parameters
        ----------
        pwd : str
            パスワード
            12桁の文字列
        """
        if len(pwd) != 12:
            raise ValueError("Password length must be 12.")
        self._writeAndReadline("SKSETPWD C " + pwd, "OK")

    def execSetRbId(self, rbid):
        """
        Route-B IDを登録する

        SKSETRBIDを実行してBルートIDを登録する

        Parameters
        ----------
        rbid : str
            Route-B ID
            32桁の文字列
        """
        if len(rbid) != 32:
            raise ValueError("Route-B ID length must be 32.")
        self._writeAndReadline("SKSETRBID " + rbid, "OK")

    def execScan(self):
        """
        チャンネルスキャンを実行する

        SKSCANを実行してチャンネルをスキャンする

        Returns
        -------
        dict
            EPANDESCイベントで通知された内容のdict
            以下のkeyを持つ
                Channel
                Channel Page
                Pan ID
                Addr
                LQI
                PairID

        Raises
        -------
        ReadTimeoutError
            規定の時間内に期待する応答を全て読み込めなかった場合に発生する例外
        """
        response = self._writeAndReadline(
            "SKSCAN 2 FFFFFFFF 6",
            max_retry=self.SCAN_RETRY_COUNT,
            retry_wait=self.SCAN_RETRY_WAIT_TIME_MS,
            pre_wait=self.SCAN_READ_WAIT_TIME_MS
        )
        kv = {
            "Channel": None,
            "Channel Page": None,
            "Pan ID": None,
            "Addr": None,
            "LQI": None,
            "PairID": None,
        }
        for line in response:
            for k in kv.keys():
                if k + ":" in line:
                    _, val = line.split(":", 2)
                    kv[k] = val
                    break
        self._logging.info(kv)
        if None in kv.values():
            raise ReadTimeoutError("Read timed out. (SKSCAN)")
        return kv

    def execSetChannel(self, channel):
        """
        使用する論理チャンネル番号を設定する

        SKSREG S2コマンドを実行して使用する論理チャンネル番号を設定する

        Parameters
        ----------
        channel : str
            使用する論理チャンネル番号
            16進数表記の2桁の文字列(8bit)
            21-3C
        """
        self._writeAndReadline("SKSREG S2 " + channel, "OK")

    def execSetPanId(self, panId):
        """
        端末のPAN IDを設定する

        SKSREG S3コマンドを実行してPAN IDを設定する

        Parameters
        ----------
        panId : str
            PAN ID
            16進数表記の4桁の文字列(16bit)
            0000-FFFF
        """
        self._writeAndReadline("SKSREG S3 " + panId, "OK")

    def execConvertAddress(self, mac_address):
        """
        MACアドレスをIPv6アドレスに変換する

        SKLL64コマンドを実行してMACアドレスをIPv6リンクローカルアドレスに変換した結果を取得する

        Parameters
        ----------
        mac_address : str
            MACアドレス
            16進数表記の16桁の文字列

        Returns
        -------
        str
            IPv6リンクローカルアドレス
            16進数表記4桁文字列を8個を":"で連結した文字列
        """
        response = self._writeAndReadline("SKLL64 " + mac_address, ":")
        return response[-1]

    def execJoin(self, ip_address):
        """
        指定されたIPアドレスに対して接続を行う

        SKJOINコマンドを実行して指定されたIPアドレスに対して接続シーケンスを開始する

        Parameters
        ----------
        ip_address : str
            接続先のIPv6アドレス

        Raises
        -------
        ConnectionError
            接続が完了しなかった場合に発生する
            設定情報(認証情報)が間違っていた場合など
        """
        response = self._writeAndReadline(
            "SKJOIN " + ip_address,
            ["EVENT 24", "EVENT 25"],
            max_retry=self.JOIN_RETRY_COUNT,
            retry_wait=self.JOIN_RETRY_WAIT_TIME_MS
        )
        last_line = response[-1]
        if last_line.startswith("EVENT 25"):  # 接続完了
            self._ip_address = ip_address
            return
        # 接続過程でエラー
        raise ConnectionError("Connection failed.")

    def execGetStatus(self):
        """
        スマートメータから動作状態を取得する

        スマートメータに対して動作状態(EPC=0x80)を問い合わせて結果を返す

        Returns
        -------
        bool | None
            On(0x30)の場合Trueを返す
            Off(0x31)の場合Falseを返す
            それ以外の場合はNoneを返す
        """
        edt = self._requestEDTAsIntFromSmartMeter(self._ip_address, 0x80)
        if edt == 0x30:
            return True
        elif edt == 0x31:
            return False
        return None

    def execGetFactor(self):
        """
        スマートメータから係数を取得する

        スマートメータに対して係数(EPC=0xD3)を問い合わせて結果を返す
        積算電力計測値, 履歴を実使用量に換算する際に使用する

        Returns
        -------
        int | None
            係数(10進数で最大6桁 0-999999)
            応答を得られなかった場合はNone
        """
        return self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xD3)

    def execGetSignificantFigures(self):
        """
        スマートメータから積算電力量有効桁数を取得する

        スマートメータに対して積算電力量有効桁数(EPC=0xD7)を問い合わせて結果を返す

        Returns
        -------
        int | None
            有効桁数(1-8)
            応答を得られなかった場合はNone
        """
        return self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xD7)

    def execGetIntegralPowerConsumption(self):
        """
        スマートメータから積算電力量を取得する

        スマートメータに対して積算電力量計測値(EPC=0xE0)を問い合わせて結果を返す

        Returns
        -------
        int | None
            kWh
            積算電力量計測値(最大8桁)から係数と単位を用いて計算された値
            応答を得られなかった場合はNone
        """
        return self._calcPowerConsumption(self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xE0))

    def execGetIntegralPowerConsumptionUnit(self):
        """
        スマートメータから積算電力量単位を取得する

        スマートメータに対して積算電力量単位(EPC=0xE1)を問い合わせて結果を返す

        Returns
        -------
        float | None
            積算電力量単位(kWh)
            応答を得られなかった場合はNone
        """
        edt = self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xE1)
        if edt == 0x00:
            return 1
        elif edt == 0x01:
            return 0.1
        elif edt == 0x02:
            return 0.01
        elif edt == 0x03:
            return 0.001
        elif edt == 0x04:
            return 0.0001
        elif edt == 0x0A:
            return 10
        elif edt == 0x0B:
            return 100
        elif edt == 0x0C:
            return 1000
        elif edt == 0x0D:
            return 10000
        return None

    def execGetCurrentPowerConsumption(self):
        """
        スマートメータから瞬時電力計測値を取得する

        スマートメータに対して瞬時電力計測値(EPC=0xE7)を問い合わせて結果を返す

        Returns
        -------
        int | None
            瞬時電力計測値(W)
            応答を得られなかった場合はNone
        """
        return self._convertUnsignedToSigned(self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xE7), 32)

    def execGetCurrentAmpere(self):
        """
        スマートメータから瞬時電流計測値を取得する

        スマートメータに対して瞬時電流計測値(EPC=0xE8)を問い合わせて結果を返す

        Returns
        -------
        tuple(int, int) | None
            瞬時電流計測値(0.1A)
            (R相, T相)
            単相2線式の場合T相の値はNone
            応答を得られなかった場合はNone
        """
        edt = self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xE8)
        if edt is None:
            return None
        r = self._convertUnsignedToSigned((edt >> 16) & 0xFFFF, 16)
        t = self._convertUnsignedToSigned(edt & 0xFFFF, 16)
        if t == 0x7FFE:
            t = None
        return (r, t)

    def execGetLast30MinutesPowerConsumption(self):
        """
        スマートメータから定時積算電力量を取得する

        スマートメータに対して定時積算電力量計測値(EPC=0xEA)を問い合わせて結果を返す
        最新の30分ごとの計測時刻における積算電力量計測値が取得できる

        Returns
        -------
        dict | None
            日時と計測値のdict
            year : int
                1-9999
            mon : int
                1-12
            mday : int
                1-31
            hour : int
                0-23
            min : int
                0-59
            sec : int
                0-59
            power : int
                kWh
                積算電力量計測値から係数と単位を用いて計算された値
            応答を得られなかった場合はNone
        """
        frame = self._createEchonetLiteFrame(epc=0xEA, tid=self._nextTransactionId())
        search_frames = self._createBreakWordsFromFrame(frame)
        response_frame = self._findFrameFromResponseEvents(self._sendUDPData(self._ip_address, frame, search_frames), frame)
        if response_frame is None:
            return None
        edt = response_frame["EDT"]
        if edt is None:
            return None
        result = {}
        result["year"]  = int(edt[0:4], 16)
        result["mon"]   = int(edt[4:6], 16)
        result["mday"]  = int(edt[6:8], 16)
        result["hour"]  = int(edt[8:10], 16)
        result["min"]   = int(edt[10:12], 16)
        result["sec"]   = int(edt[12:14], 16)
        result["power"] = self._calcPowerConsumption(int(edt[14:22], 16))
        self._logging.debug(result)
        return result

    def execSetTargetDayForHistory(self, day):
        """
        スマートメータから履歴を収集する際の対象日を設定する

        スマートメータから積算電力量計測履歴を収集する際の対象日(0xE5)を設定する
        99日前まで設定できるが実際に履歴を取得できたのは45日前までだった

        Parameters
        ----------
        day : int
            対象日(0-99)
            0:当日, 1:前日, 2:2日前...

        Returns
        -------
        bool
            設定が完了した場合はTrue
            完了したか不明な場合はFalse
        """
        edt = day.to_bytes(1, 'big')
        frame = self._createEchonetLiteFrame(epc=0xE5, tid=self._nextTransactionId(), esv=0x61, edt=edt)
        search_frames = self._createBreakWordsFromFrame(frame)
        response_frame = self._findFrameFromResponseEvents(self._sendUDPData(self._ip_address, frame, search_frames), frame)
        if response_frame is None:
            return False
        return True

    def execGetTargetDayForHistory(self):
        """
        スマートメータから履歴を収集する際の対象日を取得する

        スマートメータに設定された積算電力量計測履歴を収集する際の対象日(0xE5)を取得する

        Returns
        -------
        int | None
            対象日(0-99)
            応答を得られなかった場合はNone
        """
        return self._requestEDTAsIntFromSmartMeter(self._ip_address, 0xE5)

    def execGetPowerConsumptionHistory(self):
        """
        スマートメータから指定日の24時間積算電力の履歴を取得する

        スマートメータに対して積算電力量計測値履歴1(0xE2)を問い合わせて結果を返す
        問い合わせ対象の日付指定はexecSetTargetDayForHistory()で事前に行う

        Returns
        -------
        dict | None
            対象日と履歴のdict
            day : int
                対象日(0-99)
                0:当日, 1:前日, 2:2日前...
            powers : list
                kWhのlist
                積算電力量計測値から係数と単位を用いて計算された値
                対象日の30分ごと48コマ分
                00:00, 00:30, 01:00...
                未測定のコマはNone
        """
        frame = self._createEchonetLiteFrame(epc=0xE2, tid=self._nextTransactionId())
        search_frames = self._createBreakWordsFromFrame(frame)
        response_frame = self._findFrameFromResponseEvents(self._sendUDPData(self._ip_address, frame, search_frames), frame)
        if response_frame is None:
            return None
        edt = response_frame["EDT"]
        if edt is None:
            return None
        result = {
            "day": int(edt[0:4], 16)
        }
        powers = []
        for i in range(48):
            offset = 4 + i * 8
            power = int(edt[offset:offset+8], 16)
            if power > 99999999:
                """
                未測定の場合はNone
                値の範囲は 0x05F5E0FF(99999999) までなので超えていたら未測定とみなす
                仕様書に明記はないが実環境では未測定の場合 0xFFFFFFFE(4294967294) が設定されていた
                """
                powers.append(None)
            else:
                powers.append(self._calcPowerConsumption(power))
        result["powers"] = powers
        self._logging.debug(result)
        return result

    def setPowerConsumptionCalcParams(self, *, factor, unit):
        """
        積算電力量を計算するためのパラメータを設定する

        スマートメータから取得した積算電力計測値をkWhに変換するためのパラメータを設定する

        Parameters
        ----------
        factor : int
            係数
            execGetFactor() で取得できる値
        unit : fload
            積算電力量単位
            execGetIntegralPowerConsumptionUnit() で取得できる値
        """
        self._factor = factor
        self._unit = unit

    def _calcPowerConsumption(self, val):
        """
        スマートメータから取得した積算電力量計測値をkWhに変換する

        設定された係数と単位から計測値をkWhに変換する

        Parameters
        ----------
        val : int | None
            計測値

        Returns
        -------
        float | None
            計算されたkWh
        """
        if val is None:
            return None
        return val * self._factor * self._unit

    def getMaxIntegralPowerConsumption(self, significant_figures):
        """
        積算電力量の最大値を返す

        スマートメータから取得できる積算電力量の最大値を返す
        積算電力量の計測値が最大値を超えて0からの再カウントになった際の計算に使用する

        Parameters
        ----------
        significant_figures : int
            有効桁数(1-8)
            execGetSignificantFigures() で取得できる値

        Returns
        -------
        float
            積算電力量の最大値
            計測値の最大値ではなく計算されたkWhの最大値
        """
        return self._calcPowerConsumption(10 ** significant_figures - 1)

class DeviceError(Exception):
    """
    BP35A1デバイスに関連する例外
    """
    pass

class ReadTimeoutError(DeviceError):
    """
    デバイス関連の処理で読み込みが規定の時間で終わらなかった場合の例外
    """
    pass

class UnexpectedResponseError(DeviceError):
    """
    デバイスからの応答内容が期待した形式ではない場合の例外
    """
    pass

class ConnectionError(DeviceError):
    """
    接続に失敗した場合の例外
    """
    pass

class UndefinedAddressError(DeviceError):
    """
    IPv6アドレスが未定義の場合の例外

    SKJOINによるセッションが開始されていない状態でコマンドを実行した場合に発生する
    """
    pass

# <<< wisun
