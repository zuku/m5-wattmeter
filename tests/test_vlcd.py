import unittest
from unittest.mock import MagicMock, call
from mock import lcd as lcd_mock, axp, wmstate
import vlcd as virtual_lcd

class TestVLCD(unittest.TestCase):
    def test_init(self):
        lcd = lcd_mock
        screen_w = 136
        screen_h = 241
        lcd.screensize = MagicMock(return_value=(screen_w, screen_h))
        lcd.sprite_create = MagicMock()
        lcd.font = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        self.assertEqual(vlcd._lcd, lcd)
        self.assertEqual(vlcd._flip, False)
        self.assertEqual(vlcd._fg, lcd.WHITE)
        self.assertEqual(vlcd._bg, lcd.BLACK)
        self.assertEqual(vlcd._current_font, lcd.FONT_Default)
        self.assertEqual(vlcd._current_face_index, 0)
        self.assertEqual(vlcd._screen_w, screen_w)
        self.assertEqual(vlcd._screen_h, screen_h)
        margin_bottom = virtual_lcd.VirtualLCD.MARGIN_BOTTOM
        lcd.sprite_create.assert_called_with(screen_w, screen_h + margin_bottom, lcd.SPRITE_8BIT)
        lcd.font.assert_called_once_with(lcd.FONT_Default, rotate = 270, color = lcd.WHITE)

    def test_pixel(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.pixel = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._pixel(100, 50, lcd.BLUE)
        lcd.pixel.assert_called_once_with(50, 141, color=lcd.BLUE)

    def test_pixel_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.pixel = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        vlcd._pixel(100, 50, lcd.BLUE)
        lcd.pixel.assert_called_once_with(86, 100, color=lcd.BLUE)

    def test_rect(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.rect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._rect(15, 5, 30, 60, lcd.BLUE, lcd.YELLOW)
        lcd.rect.assert_called_once_with(5, 196, 60, 30, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_rect_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.rect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        vlcd._rect(15, 5, 30, 60, lcd.BLUE, lcd.YELLOW)
        lcd.rect.assert_called_once_with(71, 15, 60, 30, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_roundRect(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.roundrect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._roundRect(15, 5, 30, 60, 6, lcd.BLUE, lcd.YELLOW)
        lcd.roundrect.assert_called_once_with(5, 196, 60, 30, 6, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_roundRect_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.roundrect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        vlcd._roundRect(15, 5, 30, 60, 6, lcd.BLUE, lcd.YELLOW)
        lcd.roundrect.assert_called_once_with(71, 15, 60, 30, 6, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_triangle(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.triangle = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._triangle(0, 5, 30, 10, 25, 20, lcd.BLUE, lcd.YELLOW)
        lcd.triangle.assert_called_once_with(5, 241, 10, 211, 20, 216, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_triangle_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.triangle = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        vlcd._triangle(0, 5, 30, 10, 25, 20, lcd.BLUE, lcd.YELLOW)
        lcd.triangle.assert_called_once_with(131, 0, 126, 30, 116, 25, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_circle(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.circle = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._circle(100, 30, 10, lcd.BLUE, lcd.YELLOW)
        lcd.circle.assert_called_once_with(30, 141, 10, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_circle_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.circle = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        vlcd._circle(100, 30, 10, lcd.BLUE, lcd.YELLOW)
        lcd.circle.assert_called_once_with(106, 100, 10, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_arc(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.arc = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._arc(100, 30, 10, 2, 90, 180, lcd.BLUE, lcd.YELLOW)
        lcd.arc.assert_called_once_with(30, 141, 10, 2, 0, 90, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_arc_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))
        lcd.arc = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        vlcd._arc(100, 30, 10, 2, 90, 180, lcd.BLUE, lcd.YELLOW)
        lcd.arc.assert_called_once_with(106, 100, 10, 2, 180, 270, color=lcd.BLUE, fillcolor=lcd.YELLOW)

    def test_convertCoordinates(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        self.assertEqual(vlcd._convertCoordinates(0, 0), (0, 241))
        self.assertEqual(vlcd._convertCoordinates(0, 68), (68, 241))
        self.assertEqual(vlcd._convertCoordinates(0, 136), (136, 241))
        self.assertEqual(vlcd._convertCoordinates(120, 0), (0, 121))
        self.assertEqual(vlcd._convertCoordinates(241, 0), (0, 0))
        self.assertEqual(vlcd._convertCoordinates(120, 68), (68, 121))
        self.assertEqual(vlcd._convertCoordinates(241, 136), (136, 0))

    def test_convertCoordinates_flip(self):
        lcd = lcd_mock
        lcd.screensize = MagicMock(return_value=(136, 241))

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)
        self.assertEqual(vlcd._convertCoordinates(0, 0), (136, 0))
        self.assertEqual(vlcd._convertCoordinates(0, 68), (68, 0))
        self.assertEqual(vlcd._convertCoordinates(0, 136), (0, 0))
        self.assertEqual(vlcd._convertCoordinates(120, 0), (136, 120))
        self.assertEqual(vlcd._convertCoordinates(241, 0), (136, 241))
        self.assertEqual(vlcd._convertCoordinates(120, 68), (68, 120))
        self.assertEqual(vlcd._convertCoordinates(241, 136), (0, 241))

    def test_normalizeAngle(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        self.assertEqual(vlcd._normalizeAngle(0, 0), 0)
        self.assertEqual(vlcd._normalizeAngle(0, 180), 180)
        self.assertEqual(vlcd._normalizeAngle(0, 360), 360)
        self.assertEqual(vlcd._normalizeAngle(180, 360), 180)
        self.assertEqual(vlcd._normalizeAngle(0, -270), 90)

    def test_createColorArgs(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        self.assertEqual(vlcd._createColorArgs(), {})
        self.assertEqual(vlcd._createColorArgs(lcd.BLACK), {"color": lcd.BLACK})
        self.assertEqual(vlcd._createColorArgs(lcd.BLACK, lcd.RED), {"color": lcd.BLACK, "fillcolor": lcd.RED})

    def test_setFlip(self):
        lcd = lcd_mock
        lcd.font = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.font.reset_mock()
        vlcd.setFlip(True)
        self.assertEqual(vlcd._flip, True)
        lcd.font.assert_called_once_with(lcd.FONT_Default, rotate = 90, color = lcd.WHITE)

        lcd.font.reset_mock()
        vlcd.setFlip(False)
        self.assertEqual(vlcd._flip, False)
        lcd.font.assert_called_once_with(lcd.FONT_Default, rotate = 270, color = lcd.WHITE)

    def test_setBrightness(self):
        lcd = lcd_mock
        axp.setLcdBrightness = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        axp.setLcdBrightness.reset_mock()
        vlcd.setBrightness(50)
        axp.setLcdBrightness.assert_called_once_with(50)
        self.assertEqual(vlcd._brightness, 50)

    def test_sleep(self):
        lcd = lcd_mock
        axp.setLcdBrightness = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        axp.setLcdBrightness.reset_mock()
        vlcd.sleep()
        axp.setLcdBrightness.assert_called_once_with(0)

    def test_wakeUp(self):
        lcd = lcd_mock
        axp.setLcdBrightness = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        axp.setLcdBrightness.reset_mock()
        vlcd.setBrightness(33)
        axp.setLcdBrightness.assert_called_once_with(33)

        axp.setLcdBrightness.reset_mock()
        vlcd.sleep()
        axp.setLcdBrightness.assert_called_once_with(0)

        axp.setLcdBrightness.reset_mock()
        vlcd.wakeUp()
        axp.setLcdBrightness.assert_called_once_with(33)

    def test_setColor(self):
        lcd = lcd_mock
        lcd.setColor = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.setColor.reset_mock()
        vlcd.setColor(lcd.GREENYELLOW, lcd.LIGHTGREY)
        self.assertEqual(vlcd._fg, lcd.GREENYELLOW)
        self.assertEqual(vlcd._bg, lcd.LIGHTGREY)
        lcd.setColor.assert_called_once_with(lcd.GREENYELLOW, lcd.LIGHTGREY)

    def test_setFace(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        vlcd.setFace(virtual_lcd.VirtualLCD.FACE_BASIC_LIGHT)
        self.assertEqual(vlcd._current_face_index, 1)

    def test_setFace_out_of_range(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        with self.assertRaises(ValueError):
            vlcd.setFace(99999999)

    def test_nextFace(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        face_list = virtual_lcd.VirtualLCD.FACE_LIST
        for i in face_list[1:]:
            self.assertEqual(vlcd.nextFace(), face_list[i])
        self.assertEqual(vlcd.nextFace(), face_list[0])

    def test_showError(self):
        lcd = lcd_mock
        lcd.clear = MagicMock()
        lcd.font = MagicMock()
        lcd.text = MagicMock()
        lcd.rect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.font.reset_mock()
        lcd.text.reset_mock()
        lcd.rect.reset_mock()
        message = "Test Error Message"
        vlcd.showError(message)
        lcd.clear.assert_called_once_with(lcd.BLACK)
        font_calls = [
            call(lcd.FONT_Arial16, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=270, color=lcd.WHITE)
        ]
        lcd.font.assert_has_calls(font_calls)
        lcd.rect.assert_called_once_with(21, 5, 6, 231, color=lcd.RED, fillcolor=lcd.RED)
        text_calls = [
            call(5, 236, "Error", color=lcd.WHITE),
            call(30, 236, message, color=lcd.WHITE)
        ]
        lcd.text.assert_has_calls(text_calls)

    def test_showError_flip(self):
        lcd = lcd_mock
        lcd.clear = MagicMock()
        lcd.font = MagicMock()
        lcd.text = MagicMock()
        lcd.rect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)

        lcd.font.reset_mock()
        lcd.text.reset_mock()
        lcd.rect.reset_mock()
        message = "Test Error Message"
        vlcd.showError(message)
        lcd.clear.assert_called_once_with(lcd.BLACK)
        font_calls = [
            call(lcd.FONT_Arial16, rotate=90, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=90, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=90, color=lcd.WHITE)
        ]
        lcd.font.assert_has_calls(font_calls)
        lcd.rect.assert_called_once_with(109, 5, 6, 231, color=lcd.RED, fillcolor=lcd.RED)
        text_calls = [
            call(131, 5, "Error", color=lcd.WHITE),
            call(106, 5, message, color=lcd.WHITE)
        ]
        lcd.text.assert_has_calls(text_calls)

    def test_showError_multi_line(self):
        lcd = lcd_mock
        lcd.clear = MagicMock()
        lcd.font = MagicMock()
        lcd.text = MagicMock()
        lcd.rect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.font.reset_mock()
        lcd.text.reset_mock()
        lcd.rect.reset_mock()
        messages = [
            "Test Error Message 1",
            "Test Error Message 2",
        ]
        vlcd.showError("\n".join(messages))
        lcd.clear.assert_called_once_with(lcd.BLACK)
        font_calls = [
            call(lcd.FONT_Arial16, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=270, color=lcd.WHITE)
        ]
        lcd.font.assert_has_calls(font_calls)
        lcd.rect.assert_called_once_with(21, 5, 6, 231, color=lcd.RED, fillcolor=lcd.RED)
        text_calls = [
            call(5, 236, "Error", color=lcd.WHITE),
            call(30, 236, messages[0], color=lcd.WHITE),
            call(44, 236, messages[1], color=lcd.WHITE)
        ]
        lcd.text.assert_has_calls(text_calls)

    def test_showError_with_title(self):
        lcd = lcd_mock
        lcd.clear = MagicMock()
        lcd.font = MagicMock()
        lcd.text = MagicMock()
        lcd.rect = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.font.reset_mock()
        lcd.text.reset_mock()
        lcd.rect.reset_mock()
        title = "TEST ERROR"
        message = "Test Error Message"
        vlcd.showError(message, title)
        lcd.clear.assert_called_once_with(lcd.BLACK)
        font_calls = [
            call(lcd.FONT_Arial16, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Default, rotate=270, color=lcd.WHITE)
        ]
        lcd.font.assert_has_calls(font_calls)
        lcd.rect.assert_called_once_with(21, 5, 6, 231, color=lcd.RED, fillcolor=lcd.RED)
        text_calls = [
            call(5, 236, title, color=lcd.WHITE),
            call(30, 236, message, color=lcd.WHITE)
        ]
        lcd.text.assert_has_calls(text_calls)

    def test_showProgress(self):
        lcd = lcd_mock
        lcd.clear = MagicMock()
        lcd.font = MagicMock()
        lcd.text = MagicMock()
        lcd.rect = MagicMock()
        lcd.circle = MagicMock()
        lcd.arc = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.font.reset_mock()
        lcd.text.reset_mock()
        lcd.rect.reset_mock()
        lcd.circle.reset_mock()
        lcd.arc.reset_mock()
        vlcd.showProgress(0.5, "detail")
        lcd.clear.assert_called_once_with(lcd.BLACK)
        lcd.arc.assert_called_once_with(48, 121, 40, 20, 270, 90, color=lcd.WHITE, fillcolor=lcd.WHITE)
        circle_calls = [
            call(48, 121, 40, color=lcd.WHITE),
            call(48, 121, 20, color=lcd.WHITE)
        ]
        lcd.circle.assert_has_calls(circle_calls)
        font_calls = [
            call(lcd.FONT_Arial12, rotate=270, color=lcd.WHITE),
            call(lcd.FONT_Arial16, rotate=270, color=lcd.WHITE)
        ]
        lcd.font.assert_has_calls(font_calls)
        text_calls = [
            call(93, 171, " 50%", color=lcd.WHITE),
            call(108, 171, "detail", color=lcd.WHITE)
        ]
        lcd.text.assert_has_calls(text_calls)

    def test_showProgress_flip(self):
        lcd = lcd_mock
        lcd.clear = MagicMock()
        lcd.font = MagicMock()
        lcd.text = MagicMock()
        lcd.rect = MagicMock()
        lcd.circle = MagicMock()
        lcd.arc = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd.setFlip(True)

        lcd.font.reset_mock()
        lcd.text.reset_mock()
        lcd.rect.reset_mock()
        lcd.circle.reset_mock()
        lcd.arc.reset_mock()
        vlcd.showProgress(0.5, "detail")
        lcd.clear.assert_called_once_with(lcd.BLACK)
        lcd.arc.assert_called_once_with(88, 120, 40, 20, 90, 270, color=lcd.WHITE, fillcolor=lcd.WHITE)
        circle_calls = [
            call(88, 120, 40, color=lcd.WHITE),
            call(88, 120, 20, color=lcd.WHITE)
        ]
        lcd.circle.assert_has_calls(circle_calls)
        font_calls = [
            call(lcd.FONT_Arial12, rotate=90, color=lcd.WHITE),
            call(lcd.FONT_Arial16, rotate=90, color=lcd.WHITE)
        ]
        lcd.font.assert_has_calls(font_calls)
        text_calls = [
            call(43, 70, " 50%", color=lcd.WHITE),
            call(28, 70, "detail", color=lcd.WHITE)
        ]
        lcd.text.assert_has_calls(text_calls)

    def test_showProgress_0_percent(self):
        lcd = lcd_mock
        lcd.text = MagicMock()
        lcd.arc = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.text.reset_mock()
        lcd.arc.reset_mock()
        vlcd.showProgress(0)
        lcd.arc.assert_called_once_with(48, 121, 40, 20, 270, 271, color=lcd.WHITE, fillcolor=lcd.WHITE)
        lcd.text.assert_called_once_with(93, 171, "  0%", color=lcd.WHITE)

    def test_showProgress_100_percent(self):
        lcd = lcd_mock
        lcd.text = MagicMock()
        lcd.arc = MagicMock()

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)

        lcd.text.reset_mock()
        lcd.arc.reset_mock()
        vlcd.showProgress(1)
        lcd.arc.assert_called_once_with(48, 121, 40, 20, 270, 269, color=lcd.WHITE, fillcolor=lcd.WHITE)
        lcd.text.assert_called_once_with(93, 171, "100%", color=lcd.WHITE)

    def test_faceBasicDark(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._faceBasicDark = MagicMock()
        vlcd.setFace(vlcd.FACE_BASIC_DARK)
        vlcd.update(wmstate)

        vlcd._faceBasicDark.assert_called_once()

    def test_faceBasicLight(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._faceBasicLight = MagicMock()
        vlcd.setFace(vlcd.FACE_BASIC_LIGHT)
        vlcd.update(wmstate)

        vlcd._faceBasicLight.assert_called_once()

    def test_faceBargraph(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._faceBargraph = MagicMock()
        vlcd.setFace(vlcd.FACE_BARGRAPH)
        vlcd.update(wmstate)

        vlcd._faceBargraph.assert_called_once()

    def test_face7seg(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._face7seg = MagicMock()
        vlcd.setFace(vlcd.FACE_7SEG)
        vlcd.update(wmstate)

        vlcd._face7seg.assert_called_once()

    def test_faceHakone(self):
        lcd = lcd_mock

        vlcd = virtual_lcd.VirtualLCD(lcd=lcd, axp=axp)
        vlcd._faceHakone = MagicMock()
        vlcd.setFace(vlcd.FACE_HAKONE)
        vlcd.update(wmstate)

        vlcd._faceHakone.assert_called_once()
