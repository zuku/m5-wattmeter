# vlcd >>>

class VirtualLCD:
    """
    M5StickC Plusの仮想LCDクラス

    lcd.sprite_* を使用する際に発生する諸々の問題を回避するためlcdを間接的に使用するクラス

    Examples
    --------
    from m5stack import lcd, axp

    vlcd = VirtualLCD(lcd=lcd, axp=axp)
    vlcd.setFlip(False)
    vlcd.setBrightness(50)

    Attributes
    ----------
    MARGIN_BOTTOM : int
        画面下部のマージン(ピクセル数)
        画面サイズと同一のspriteを生成すると最下部(LANDSCAPE相当の表示時での左端)でのテキスト描画が行われなくなる
        この問題を回避するため下部にマージンを設定する
    DEFAULT_BRIGHTNESS : int
        画面のデフォルトの輝度
    FACE_* : int
        表示方式
    FACE_LIST : tuple
        使用可能な表示方式のリスト
    """

    MARGIN_BOTTOM = 72

    DEFAULT_BRIGHTNESS = 60

    FACE_BASIC_DARK  = 0
    FACE_BASIC_LIGHT = 1
    FACE_BARGRAPH    = 2
    FACE_7SEG        = 3
    FACE_HAKONE      = 4

    FACE_LIST = (
        FACE_BASIC_DARK,
        FACE_BASIC_LIGHT,
        FACE_BARGRAPH,
        FACE_7SEG,
        FACE_HAKONE,
    )

    def __init__(self, *, lcd, axp):
        """
        Parameters
        ----------
        lcd : object
            lcdモジュール
        axp : object
            axpモジュール
        """
        self._lcd = lcd
        self._axp = axp
        self._flip = False
        self.setColor(lcd.WHITE, lcd.BLACK)
        self._brightness = self.DEFAULT_BRIGHTNESS
        self._current_font = lcd.FONT_Default
        self._current_face_index = 0
        self._current_face_func = self._faceBasicDark

        screen_w, screen_h = lcd.screensize()
        lcd.sprite_create(screen_w, screen_h + self.MARGIN_BOTTOM, lcd.SPRITE_8BIT)
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._vscreen_w = screen_h
        self._vscreen_h = screen_w

        self._resetOrientation()

    def _resetOrientation(self):
        """
        画面の向きを現在の設定に従いリセットする
        """
        self._font()

    def _font(self, font = None, rotate = 0):
        """
        使用するFontを設定する

        Parameters
        ----------
        font : int
            使用するフォントを指定する
            lcd.FONT_*
        rotate : int
            文字の回転角度(時計回り)を指定する
            0-360
        """
        rotate = self._normalizeAngle(rotate, 90 if self._flip else 270)
        font = font if font is not None else self._current_font
        self._lcd.font(font, rotate = rotate, color = self._fg)
        self._current_font = font

    def _text(self, x, y, text, color = -1):
        """
        文字列textを描画する

        Parameters
        ----------
        x : int
            文字の水平方向の描画開始位置を指定する
        y : int
            文字の垂直方向の描画開始位置を指定する
        text : str
            描画する文字列
        color : int
            文字の色
            指定しない場合は現在の前景色
        """
        actual_x, actual_y = self._convertCoordinates(x, y)
        kwargs = self._createColorArgs(color)
        self._lcd.text(actual_x, actual_y, text, **kwargs)

    def _pixel(self, x, y, color = -1):
        """
        x,yの位置にピクセルを描画する

        Parameters
        ----------
        x : int
            水平方向の描画位置
        y : int
            垂直方向の描画位置
        color : int
            描画するピクセルの色
        """
        actual_x, actual_y = self._convertCoordinates(x, y)
        kwargs = self._createColorArgs(color)
        self._lcd.pixel(actual_x, actual_y, **kwargs)

    def _rect(self, x, y, width, height, color = -1, fillcolor = -1):
        """
        x,yを左上の頂点として幅width, 高さheightの方形を描画する

        Parameters
        ----------
        x : int
            方形の左上の水平位置
        y : int
            方形の左上の垂直位置
        width : int
            方形の水平方向の大きさ
        height : int
            方形の垂直方向の大きさ
        color : int
            方形の外周の色
        fillcolor : int
            方形の内側を塗りつぶす色
        """
        lcd = self._lcd
        actual_x, actual_y = self._convertCoordinates(x, y)
        if self._flip:
            actual_x -= height
        else:
            actual_y -= width
        kwargs = self._createColorArgs(color, fillcolor)
        lcd.rect(actual_x, actual_y, height, width, **kwargs)

    def _roundRect(self, x, y, width, height, r, color = -1, fillcolor = -1):
        """
        x,yを左上の頂点として幅width, 高さheight 角の丸み半径rの方形を描画する

        Parameters
        ----------
        x : int
            方形の左上の水平位置
        y : int
            方形の左上の垂直位置
        width : int
            方形の水平方向の大きさ
        height : int
            方形の垂直方向の大きさ
        r : int
            方形の角の丸み半径
        color : int
            方形の外周の色
        fillcolor : int
            方形の内側を塗りつぶす色
        """
        lcd = self._lcd
        actual_x, actual_y = self._convertCoordinates(x, y)
        if self._flip:
            actual_x -= height
        else:
            actual_y -= width
        kwargs = self._createColorArgs(color, fillcolor)
        lcd.roundrect(actual_x, actual_y, height, width, r, **kwargs)

    def _triangle(self, x1, y1, x2, y2, x3, y3, color = -1, fillcolor = -1):
        """
        (x1,y1),(x2,y2),(x3,y3)を結ぶ三角形を描画する

        Parameters
        ----------
        x1 : int
            三角形の頂点1のx座標
        y1 : int
            三角形の頂点1のy座標
        x2 : int
            三角形の頂点2のx座標
        y2 : int
            三角形の頂点2のy座標
        x3 : int
            三角形の頂点3のx座標
        y3 : int
            三角形の頂点3のy座標
        color : int
            三角形の外周の色
        fillcolor : int
            三角形の内側を塗りつぶす色
        """
        lcd = self._lcd
        actual_x1, actual_y1 = self._convertCoordinates(x1, y1)
        actual_x2, actual_y2 = self._convertCoordinates(x2, y2)
        actual_x3, actual_y3 = self._convertCoordinates(x3, y3)
        kwargs = self._createColorArgs(color, fillcolor)
        lcd.triangle(actual_x1, actual_y1, actual_x2, actual_y2, actual_x3, actual_y3, **kwargs)

    def _circle(self, x, y, r, color = -1, fillcolor = -1):
        """
        x,yを中心とした半径rの円を描画する

        Parameters
        ----------
        x : int
            円の中心の水平位置
        y : int
            円の中心の垂直位置
        r : int
            円の半径
        color : int
            円の外周の色
        fillcolor : int
            円の内部を塗りつぶす色
        """
        lcd = self._lcd
        actual_x, actual_y = self._convertCoordinates(x, y)
        kwargs = self._createColorArgs(color, fillcolor)
        lcd.circle(actual_x, actual_y, r, **kwargs)

    def _arc(self, x, y, r, thick, start, end, color = -1, fillcolor = -1):
        """
        x,yを中心とした半径rの円のstartからendまでの角度の円弧を描画する

        Parameters
        ----------
        x : int
            円弧の中心の水平位置
        y : int
            円弧の中心の垂直位置
        r : int
            円弧の半径
        thick : int
            円弧の幅
            半径rから中心に向かう
        start : int
            円弧の開始角度
            画面の上方向を0として時計回り
            0-360
        end : int
            円弧の終了角度
            画面の上方向を0として時計回り
            0-360
        color : int
            円弧の外周の色
        fillcolor : int
            円弧の内部を塗りつぶす色
        """
        lcd = self._lcd
        actual_x, actual_y = self._convertCoordinates(x, y)
        if self._flip:
            angle_offset = 90
        else:
            angle_offset = -90
        actual_start = self._normalizeAngle(start, angle_offset)
        actual_end = self._normalizeAngle(end, angle_offset)
        kwargs = self._createColorArgs(color, fillcolor)
        lcd.arc(actual_x, actual_y, r, thick, actual_start, actual_end, **kwargs)

    def _convertCoordinates(self, x, y):
        """
        画面の座標を仮想的なものから実際の値に変換する

        Parameters
        ----------
        x : int
            仮想画面のx座標
        y : int
            仮想画面のy座標

        Returns
        -------
        tuple (x, y)
            実際に使用する座標
        """
        if self._flip:
            actual_x = self._screen_w - y
            actual_y = x
        else:
            actual_x = y
            actual_y = self._screen_h - x
        return (actual_x, actual_y)

    def _normalizeAngle(self, angle, offset = 0):
        """
        角度を正規化する

        Parameters
        ----------
        angle : int
            元になる角度
        offset : int
            表示のために回転する角度

        Returns
        -------
        int
            正規化された角度
            0-360
        """
        angle += offset
        while angle < 0:
            angle += 360
        while angle > 360:
            angle -= 360
        return angle

    def _createColorArgs(self, color = -1, fillcolor = -1):
        """
        図形描画に使用する色の引数を生成する

        Parameters
        ----------
        color : int
            色
        fillcolor : int
            塗りつぶす色

        Returns
        -------
        dict {"color": color, "fillcolor": fillcolor}
        """
        kwargs = {}
        if color >= 0:
            kwargs["color"] = color
        if fillcolor >= 0:
            kwargs["fillcolor"] = fillcolor
        return kwargs

    def _begin(self):
        """
        spriteへの描画を開始する
        """
        self._lcd.sprite_select()

    def _commit(self):
        """
        spriteへの描画を終了し画面に表示する
        """
        lcd = self._lcd
        lcd.sprite_deselect()
        lcd.sprite_show(0, 0)

    def setFlip(self, flip):
        """
        画面の上下方向を反転するかを設定する

        flip = False の場合 lcd.LANDSCAPE の表示になる
        (M5StickC Plusを縦にした時の左側が上)

        Parameters
        ----------
        flip : bool
            反転する場合はTrue
        """
        self._flip = (flip == True)
        self._resetOrientation()

    def setBrightness(self, brightness):
        """
        画面の輝度を設定する

        Parameters
        ----------
        brightness : int
            輝度 (0-100)
        """
        self._brightness = brightness
        self._axp.setLcdBrightness(brightness)

    def sleep(self):
        """
        画面を消灯してスリープ状態にする
        """
        self._axp.setLcdBrightness(0)

    def wakeUp(self):
        """
        画面を点灯してスリープ状態を解除する
        """
        self._axp.setLcdBrightness(self._brightness)

    def setColor(self, fg, bg):
        """
        表示する色を指定する

        Parameters
        ----------
        fg : int
            前景色
        bg : int
            背景色
        """
        self._fg = fg
        self._bg = bg
        self._lcd.setColor(fg, bg)

    def setFace(self, face):
        """
        使用する表示方式を設定する

        Parameters
        ----------
        face : int
            表示方式の値(FACE_*)
        """
        self._current_face_index = self.FACE_LIST.index(face)
        if face == self.FACE_BASIC_DARK:
            self._current_face_func = self._faceBasicDark
        elif face == self.FACE_BASIC_LIGHT:
            self._current_face_func = self._faceBasicLight
        elif face == self.FACE_BARGRAPH:
            self._current_face_func = self._faceBargraph
        elif face == self.FACE_7SEG:
            self._current_face_func = self._face7seg
        elif face == self.FACE_HAKONE:
            self._current_face_func = self._faceHakone
        else:
            # 未定義の場合
            self._current_face_func = self._faceBasicDark

    def nextFace(self):
        """
        次の表示方式を取得する

        使用可能な表示方式の値を順番に取得する
        リストの最後まで到達すると最初に戻る

        Returns
        -------
        int
            表示方式の値(FACE_*)
        """
        i = self._current_face_index + 1
        length = len(self.FACE_LIST)
        if i < 0 or i >= length:
            i = 0
        self._current_face_index = i
        return self.FACE_LIST[i]

    def showError(self, message, title = "Error"):
        """
        エラーメッセージを画面に表示する

        Parameters
        ----------
        message : str
            表示するエラーメッセージ
        title : str
            エラーのタイトル
            指定しない場合は Error
        """
        lcd = self._lcd
        backup_font = self._current_font
        margin = 5

        self._begin()

        lcd.clear(lcd.BLACK)
        self._font(lcd.FONT_Arial16)
        self._text(margin, margin, title, lcd.WHITE)
        self._rect(margin, margin + 16, self._vscreen_w - margin * 2, 6, color=lcd.RED, fillcolor=lcd.RED)
        self._font(lcd.FONT_Default)
        y_offset = margin + 25
        for line in message.split("\n"):
            self._text(margin, y_offset, line, lcd.WHITE)
            y_offset += 14

        self._commit()
        self.wakeUp()

        self._font(backup_font)

    def showProgress(self, percent, detail = None):
        """
        処理の進捗状況を画面に表示する

        Parameters
        ----------
        percent : double
            進捗のパーセント
            0.0-1.0
        detail : str
            進捗内容を表す短い文字列
        """
        lcd = self._lcd
        circle_x = int(self._vscreen_w / 2)
        circle_y = int(self._vscreen_h / 2) - 20
        end = int(percent * 360)
        if end < 1:
            end = 1
        elif end > 359:
            end = 359
        color = lcd.WHITE

        self._begin()
        lcd.clear(lcd.BLACK)
        self._arc(circle_x, circle_y, 40, 20, 0, end, color=color, fillcolor=color)
        self._circle(circle_x, circle_y, 40, color=color)
        self._circle(circle_x, circle_y, 20, color=color)
        self._font(lcd.FONT_Arial12)
        percent_w = lcd.textWidth("100%")
        self._text(circle_x - int(percent_w / 2), circle_y + 45, "{:3d}%".format(int(percent * 100)), color=color)
        if detail is not None:
            self._font(lcd.FONT_Arial16)
            detail_w = lcd.textWidth(detail)
            self._text(circle_x - int(detail_w / 2), circle_y + 60, detail, color=color)
        self._commit()

    def update(self, state):
        """
        表示を更新する

        設定されている現在の"FACE"で表示を更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        """
        self._current_face_func(state)

    def _faceBasic(self, state, fg, bg):
        """
        基本の表示で更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        fg : int
            前景色
        bg : int
            背景色
        """
        lcd = self._lcd
        self.setColor(fg, bg)
        self._begin()
        lcd.clear()

        self._font(lcd.FONT_DejaVu56)
        watt_s = "{:d}".format(state.getCurrentWatt())
        watt_w = lcd.textWidth(watt_s)
        # lcd.textWidth("8888") = 139
        watt_x = int((self._vscreen_w - 139) / 2 + 139 - watt_w)
        self._text(watt_x, 50, watt_s)

        self._font(lcd.FONT_DejaVu24)
        self._text(203, 74, "W")

        self._font(lcd.FONT_DejaVu18)
        time_s = state.getTime("{hour:02d}:{min:02d}")
        time_w = lcd.textWidth(time_s)
        time_x = int((self._vscreen_w - time_w) / 2)
        self._text(time_x, 10, time_s)

        self._commit()

    def _faceBasicDark(self, state):
        """
        基本の表示(ダーク)で更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        """
        lcd = self._lcd
        if state.isStatusWarning():
            self._faceBasic(state, lcd.BLACK, lcd.RED)
        elif state.isStatusCaution():
            self._faceBasic(state, lcd.BLACK, lcd.ORANGE)
        else:
            self._faceBasic(state, lcd.WHITE, lcd.BLACK)

    def _faceBasicLight(self, state):
        """
        基本の表示(ライト)で更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        """
        lcd = self._lcd
        if state.isStatusWarning():
            self._faceBasic(state, lcd.BLACK, lcd.RED)
        elif state.isStatusCaution():
            self._faceBasic(state, lcd.BLACK, lcd.ORANGE)
        else:
            self._faceBasic(state, lcd.BLACK, lcd.WHITE)

    def _faceBargraph(self, state):
        """
        グラフ付きの表示で更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        """
        lcd = self._lcd
        if state.isStatusWarning():
            fg = lcd.RED
        elif state.isStatusCaution():
            fg = lcd.YELLOW
        else:
            fg = lcd.WHITE
        bg = lcd.BLACK
        self.setColor(fg, bg)

        config_wm = state.config.config.wattmeter
        max_watt = config_wm.max.watt
        percent_current = int(state.getCurrentWatt() / max_watt * 100)
        percent_warning = None
        percent_caution = None
        if config_wm.warning is not None:
            percent_warning = int(config_wm.warning.watt / max_watt * 100)
        if config_wm.caution is not None:
            percent_caution = int(config_wm.caution.watt / max_watt * 100)

        def draw_bar(x, y, w, h, r, color, fill_percent=0):
            nonlocal lcd, bg
            colors = {"color": color}
            if fill_percent > 0.99:
                colors["fillcolor"] = color
            elif fill_percent > 0.01:
                self._roundRect(x, y, w, h, r, color, color)
                self._rect(x, y, w, int(h - h * fill_percent), bg, bg)
            self._roundRect(x, y, w, h, r, **colors)

        self._begin()
        lcd.clear()

        bar_range = 20
        for i in range(5):
            percent_bar_upper = 100 - i * bar_range
            fill_percent = (percent_current - (percent_bar_upper - bar_range)) / bar_range
            if percent_warning is not None and percent_warning < percent_bar_upper:
                color = lcd.RED
            elif percent_caution is not None and percent_caution < percent_bar_upper:
                color = lcd.YELLOW
            else:
                color = lcd.GREEN
            draw_bar(6, 7 + 26 * i, 80, 18, 5, color, fill_percent)

        # ワット数
        self._font(lcd.FONT_DejaVu40)
        watt_text = "{:d}".format(state.getCurrentWatt())
        self._text(105 + (118 - lcd.textWidth(watt_text)), 75, watt_text)
        # 単位(W)
        self._font(lcd.FONT_DejaVu18)
        self._text(210, 112, "W")
        # パーセント
        self._font(lcd.FONT_DejaVu24)
        percent_text = "{:d}%".format(percent_current)
        self._text(130 + (71 - lcd.textWidth(percent_text)), 40, percent_text)

        self._commit()

    def _face7seg(self, state):
        """
        7-segment表示で更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        """
        lcd = self._lcd
        if state.isStatusWarning():
            fg = 0xFFB536
            bg = 0x4C2012
            behind = 0x4c3112
        elif state.isStatusCaution():
            fg = 0x22272E
            bg = 0xFA9D3C
            behind = 0xE18E36
        else:
            fg = 0x22272E
            bg = 0x6D7878
            behind = 0x6C7373
        self.setColor(fg, bg)

        self._begin()
        lcd.clear()
        AltFont7seg.drawWatt(self, 3, 29, 24, 10, state.getCurrentWatt(), fg, behind)
        self._commit()

    def _faceHakone(self, state):
        """
        箱根感のある表示で更新する

        Parameters
        ----------
        state : object
            表示内容を格納したWMStateオブジェクト
        """
        lcd = self._lcd
        bg = lcd.BLACK
        behind = 0x171717
        warning_color = behind
        caution_color = behind
        normal_color = behind
        if state.isStatusWarning():
            fg = 0xD30707
            warning_color = fg
        elif state.isStatusCaution():
            fg = 0xF27713
            caution_color = fg
        else:
            fg = 0x13D9A3
            normal_color = fg
        self.setColor(fg, bg)

        def draw_16x15(x, y, bitmap, color):
            nonlocal self
            mask = 1 << 16*15
            for py in range(15):
                for px in range(16):
                    if bitmap & mask > 0:
                        self._pixel(x+px, y+py, color=color)
                    mask >>= 1

        self._begin()
        lcd.clear()
        AltFont7seg.drawDate(self, 10, 10, 10, 4, state.getTime("{mon:02d}"), state.getTime("{mday:02d}"), fg, behind)
        AltFont7seg.drawTime(self, 106, 10, 10, 4, state.getTime("{hour:02d}:{min:02d}"), fg, behind)
        AltFont7seg.drawWatt(self, 0, 53, 20, 8, state.getCurrentWatt(), fg, behind)

        # 警告
        draw_16x15(203, 14, 0x1AB07FA2303E2F687528BD3C0E431FF8FFFE1FF810081FF810081FF81008, warning_color)
        draw_16x15(220, 14, 0x08C00C8008841FFE1080608000827FFF00001FFC1008100810081FF81008, warning_color)
        self._roundRect(200, 8, 38, 25, 5, color=warning_color)
        # 注意
        draw_16x15(203, 43, 0x210010C0004008046BFE28401040104417FE604020402040204020442FFE, caution_color)
        draw_16x15(220, 43, 0x00C000843FFE041002227FFF08080FF808080FF8080002841452241227FA, caution_color)
        self._roundRect(200, 38, 38, 25, 5, color=caution_color)
        # 平常
        draw_16x15(203, 74, 0x00087FFE010021081110092009200104FFFE010001000100010001000100, normal_color)
        draw_16x15(220, 74, 0x1190091029243FFE40044FF408100FF001001FFC11081108110811380100, normal_color)
        self._roundRect(200, 68, 38, 25, 5, color=normal_color)

        self._commit()

class AltFont7seg:
    """
    代替7-segmentフォント

    lcd.FONT_7seg は以下の理由で使用できない
    * sprite上に描画しようとするとCPUパニックを起こす
    * lcd.font()のrotateパラメータを無視する

    このクラスはFONT_7segの代わりに7-segment風に描画を行う
    画面領域外に描画しようとするとCPUパニックを起こす(またはフリーズする)ので注意
    """
    FLAGS = (
        0b1110111,  # 0
        0b0010010,  # 1
        0b1011101,  # 2
        0b1011011,  # 3
        0b0111010,  # 4
        0b1101011,  # 5
        0b1101111,  # 6
        0b1010010,  # 7
        0b1111111,  # 8
        0b1111011,  # 9
    )

    @staticmethod
    def __drawHorizon(vlcd, x, y, w, h, color):
        """
        7segの水平方向のセグメントを描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標
        w : int
            セグメントの幅
        h : int
            セグメントの高さ
        color : int
            色
        """
        hh = round(h / 2)
        vlcd._triangle(x+hh, y+hh, x+h, y, x+h, y+h-1, color, color)
        vlcd._triangle(x+h+hh+w, y+hh, x+h+w, y, x+h+w, y+h-1, color, color)
        vlcd._rect(x+h, y, w, h, color, color)

    @staticmethod
    def __drawVertical(vlcd, x, y, w, h, color):
        """
        7segの垂直方向のセグメントを描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標
        w : int
            セグメントの幅
        h : int
            セグメントの高さ
        color : int
            色
        """
        hw = round(w / 2)
        vlcd._triangle(x+hw, y+hw, x+1, y+w, x+w-1, y+w, color, color)
        vlcd._triangle(x+hw, y+w+h+hw, x+1, y+w+h, x+w-1, y+w+h, color, color)
        vlcd._rect(x, y+w, w, h, color, color)

    @staticmethod
    def __getColor(flags, mask, color, behind_color):
        """
        使用する色を返す

        Parameters
        ----------
        flags : int
            描画するセグメントを示すフラグ
        mask : int
            対象セグメントをあらわすビットマスク
        color : int
            描画する場合の色
        behind_color : int
            描画しない場合の色

        Returns
        -------
        int | None
            セグメントの色
            完全に描画しない場合はNone
        """
        if flags & mask > 0:
            return color
        elif behind_color is not None:
            return behind_color
        return None

    @classmethod
    def drawMinus(cls, vlcd, x, y, w, h, color):
        """
        マイナス記号を描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標(7seg描画位置基準)
        w : int
            セグメントの幅
        h : int
            セグメントの高さ
        color : int
            色

        Returns
        -------
        int
            文字の幅
        """
        if color is not None:
            cls.__drawHorizon(vlcd, x, y+w+h+3, w, h, color)
        return 2*h+w

    @classmethod
    def drawColon(cls, vlcd, x, y, w, h, color):
        """
        コロンを描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標(7seg描画位置基準)
        w : int
            セグメントの幅
            位置の計算に使用する
        h : int
            セグメントの高さ
        color : int
            色

        Returns
        -------
        int
            文字の幅
        """
        height = 3 * h + 2 * w
        vlcd._rect(x, y+int((height / 4) - (h / 2)), h, h, color, color)
        vlcd._rect(x, y+int((height * 0.75) - (h / 2)), h, h, color, color)
        return h

    @classmethod
    def draw7seg(cls, vlcd, x, y, w, h, flags, color, behind_color = None):
        """
        7segの1文字を描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標
        w : int
            セグメントの幅
        h : int
            セグメントの高さ
        flags : int
            描画するセグメントを示すフラグ
            上位のビットから
            1: 水平上
            2: 垂直上左
            3: 垂直上右
            4: 水平中
            5: 垂直下左
            6: 垂直下右
            7: 水平下
            をあらわす
        color : int
            色
        behind_color : int
            描画しないセグメントの色

        Returns
        -------
        int
            文字の幅
        """
        c = cls.__getColor(flags, 0b1000000, color, behind_color)
        if c is not None:
            cls.__drawHorizon(vlcd, x, y, w, h, c)

        c = cls.__getColor(flags, 0b0100000, color, behind_color)
        if c is not None:
            cls.__drawVertical(vlcd, x, y+1, h, w, c)

        c = cls.__getColor(flags, 0b0010000, color, behind_color)
        if c is not None:
            cls.__drawVertical(vlcd, x+w+h, y+1, h, w, c)

        c = cls.__getColor(flags, 0b0001000, color, behind_color)
        if c is not None:
            cls.__drawHorizon(vlcd, x, y+w+h+3, w, h, c)

        c = cls.__getColor(flags, 0b0000100, color, behind_color)
        if c is not None:
            cls.__drawVertical(vlcd, x, y+5+w+h, h, w, c)

        c = cls.__getColor(flags, 0b0000010, color, behind_color)
        if c is not None:
            cls.__drawVertical(vlcd, x+w+h, y+5+w+h, h, w, c)

        c = cls.__getColor(flags, 0b0000001, color, behind_color)
        if c is not None:
            cls.__drawHorizon(vlcd, x, y+(w+h)*2+7, w, h, c)
        return 2*h+w

    @classmethod
    def drawWatt(cls, vlcd, x, y, width, height, watt, color, behind_color, *, margin=3):
        """
        7-seg形式でワット数を描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標
        width : int
            セグメントの幅
        height : int
            セグメントの高さ
        watt : int
            描画するワット数
            -9999から9999まで
        color : int
            描画するセグメントの色
        behind_color : int
            描画しないセグメントの色
        margin : int
            文字間の幅
        """
        minus_color = behind_color
        if watt < 0:
            minus_color = color
        x += cls.drawMinus(vlcd, x, y, width, height, minus_color) + margin
        watt = abs(watt)
        if watt > 9999:
            watt = 9999
        text = "{:4d}".format(watt)
        for c in text:
            if c == " ":
                flags = 0
            else:
                flags = cls.FLAGS[int(c)]
            x += cls.draw7seg(vlcd, x, y, width, height, flags, color, behind_color) + margin

    @classmethod
    def drawDate(cls, vlcd, x, y, width, height, mon, mday, color, behind_color, *, margin=3, md_margin=6):
        """
        7-seg形式で月と日を描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標
        width : int
            セグメントの幅
        height : int
            セグメントの高さ
        mon : str
            月の文字列
            数値ではなく描画する数値文字列
        mday : str
            日の文字列
            数値ではなく描画する数値文字列
        color : int
            描画するセグメントの色
        behind_color : int
            描画しないセグメントの色
        margin : int
            文字間の幅
        md_margin : int
            月と日の間の幅
        """
        for c in mon + " " + mday:
            if c == " ":
                x += md_margin
                continue
            flags = cls.FLAGS[int(c)]
            x += cls.draw7seg(vlcd, x, y, width, height, flags, color, behind_color) + margin

    @classmethod
    def drawTime(cls, vlcd, x, y, width, height, time_str, color, behind_color, *, margin=3):
        """
        7-seg形式で時刻を描画する

        Parameters
        ----------
        vlcd : object
            VirtualLCDオブジェクト
        x : int
            描画位置左上のx座標
        y : int
            描画位置左上のy座標
        width : int
            セグメントの幅
        height : int
            セグメントの高さ
        time_str : str
            時刻の文字列
        color : int
            描画するセグメントの色
        behind_color : int
            描画しないセグメントの色
        margin : int
            文字間の幅
        """
        for c in time_str:
            if c == ":":
                x += cls.drawColon(vlcd, x, y, width, height, color) + margin
            else:
                flags = cls.FLAGS[int(c)]
                x += cls.draw7seg(vlcd, x, y, width, height, flags, color, behind_color) + margin

# <<< vlcd
