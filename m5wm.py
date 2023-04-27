from m5stack import lcd, axp, btnA, btnB, speaker
import machine, utime, ujson, uos, ntptime, wifiCfg

will_remove_cache = False

def show_startup_screen():
    STARTUP_SCREEN_TIME = 5

    lcd.clear(lcd.WHITE)
    lcd.circle(68, 120, 46, color=lcd.BLACK, fillcolor=lcd.BLACK)
    lcd.triangle(29, 131, 72, 94, 76, 122, color=lcd.YELLOW, fillcolor=lcd.YELLOW)
    lcd.triangle(107, 108, 63, 145, 58, 118, color=lcd.YELLOW, fillcolor=lcd.YELLOW)

    def btnA_was_double_press():
        """
        キャッシュファイルを(後で)削除する
        """
        global will_remove_cache
        will_remove_cache = True
        speaker.sing(440)

    btnA.wasDoublePress(btnA_was_double_press)
    utime.sleep(STARTUP_SCREEN_TIME)
    btnA.restart()

def main():
    import wattmeter
    global will_remove_cache

    TASK_LOOP_WAIT_SEC = 3
    ERROR_DISPLAY_TIME = 60
    REBOOT_WAIT_SEC = 10

    logging = wattmeter.Logger
    logging.basicConfig(
        level=logging.INFO
    )

    wm = wattmeter.M5Wattmeter(
        vlcd=wattmeter.VirtualLCD(lcd=lcd, axp=axp),
        client=wattmeter.BP35A1Client(uart=machine.UART, utime=utime, logging=logging),
        config=wattmeter.WMConfig(ujson=ujson, uos=uos, logging=logging),
        logging=logging,
        wifiCfg=wifiCfg,
        utime=utime,
        ntptime=ntptime,
        speaker=speaker
    )

    if will_remove_cache:
        """
        キャッシュファイルを削除後に再起動する
        再起動しないとwm.prepare()内のキャッシュファイル生成時にパニックを起こす
        """
        logging.info("Cache file will be removed.")
        wm.config.removeCache()
        logging.info("Restart")
        machine.reset()

    def btnA_was_released():
        """
        画面の点灯/消灯を切り替える
        """
        nonlocal wm
        wm.toggleSleep()

    def btnB_was_released():
        """
        FACEを切り替える
        """
        nonlocal wm
        wm.switchFace()

    def btnB_press_for():
        """
        画面の上下を切り替える
        """
        nonlocal wm
        wm.toggleFlip()

    btnA.wasReleased(btnA_was_released)
    btnB.wasReleased(btnB_was_released)
    btnB.pressFor(2, btnB_press_for)

    prepared = False
    try:
        wm.prepare()
    except Exception as e:
        logging.exception(e)
        wm.vlcd.showError(str(e), e.__class__.__name__)
    else:
        prepared = True

    while prepared:
        try:
            while wm.execLaunchableTask():
                pass
        except Exception as e:
            logging.exception(e)
            wm.vlcd.showError(str(e), e.__class__.__name__)
            break
        utime.sleep(TASK_LOOP_WAIT_SEC)

    if wm.config.config is None:
        return

    if wm.config.config.wattmeter.auto_reboot:
        """
        auto_reboot = True の場合はエラーを一定時間表示してから再起動
        """
        utime.sleep(ERROR_DISPLAY_TIME)
        wm.vlcd.showError("Shutting down...", "Reboot")
        utime.sleep(REBOOT_WAIT_SEC)
        machine.reset()

if __name__ == "__main__":
    show_startup_screen()
    main()
