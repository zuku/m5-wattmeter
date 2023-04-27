import unittest, random
from unittest.mock import MagicMock, call
from mock import utime, logging
from mock.machine import UART
import wisun

class TestBP35A1Client(unittest.TestCase):
    def createIPv6Address(self):
        parts = [format(0xFE80 + random.randint(0, 63), '04X')]
        for _ in range(7):
            parts.append(format(random.randint(0, 0xFFFF), '04X'))
        return ':'.join(parts)

    def createMacAddress(self):
        return format(random.randint(0x0000010000000001, 0xFFFFFFFFFFFFFFFF), '016X')

    def test_init(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)

        _client = client._client
        self.assertEqual(_client._id, 1)
        self.assertEqual(_client._kwargs, {"tx": 0, "rx": 26})
        self.assertEqual(_client._baudrate, 115200)
        self.assertEqual(_client._bits, 8)
        self.assertIsNone(_client._parity)
        self.assertEqual(_client._stop, 1)
        self.assertEqual(_client._init_kwargs, {"timeout": 2000})

    def test_writeAndReadline(self):
        UART.any = MagicMock()
        UART.any.side_effect = [11, 7]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKTEST 00\r\n", "OK 00\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline("SKTEST 00", "OK")
        self.assertEqual(response, ["SKTEST 00", "OK 00"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(500)

    def test_writeAndReadline_list_break_words(self):
        UART.any = MagicMock()
        UART.any.side_effect = [11, 6]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKTEST 00\r\n", "STOP\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline("SKTEST 00", ["OK", "STOP"])
        self.assertEqual(response, ["SKTEST 00", "STOP"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(500)

    def test_writeAndReadline_tuple_break_words(self):
        UART.any = MagicMock()
        UART.any.side_effect = [11, 6]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKTEST 00\r\n", "STOP\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline("SKTEST 00", ("OK", "STOP"))
        self.assertEqual(response, ["SKTEST 00", "STOP"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(500)

    def test_writeAndReadline_no_break_words(self):
        UART.any = MagicMock()
        UART.any.side_effect = [8, 8, 0, 0, 0]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["LINE 1\r\n", "LINE 2\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline(
            "SKTEST 00",
            max_retry = 2,
            pre_wait = 300,
            retry_wait = 200
        )
        self.assertEqual(response, ["LINE 1", "LINE 2"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        sleep_ms_calls = [call(300), call(200), call(200)]
        utime.sleep_ms.assert_has_calls(sleep_ms_calls)
        self.assertEqual(utime.sleep_ms.call_count, 3)

    def test_writeAndReadline_ignore_remaining_lines(self):
        UART.any = MagicMock()
        UART.any.side_effect = [8, 4, 8]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["LINE 1\r\n", "OK\r\n", "LINE 2\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline(
            "SKTEST 00",
            "OK",
            max_retry = 2,
            pre_wait = 300,
            retry_wait = 200
        )
        self.assertEqual(response, ["LINE 1", "OK"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(300)

    def test_writeAndReadline_response_delayed(self):
        UART.any = MagicMock()
        UART.any.side_effect = [0, 8, 0, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["LINE 1\r\n", "OK\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline(
            "SKTEST 00",
            "OK",
            max_retry = 2,
            pre_wait = 300,
            retry_wait = 200
        )
        self.assertEqual(response, ["LINE 1", "OK"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        sleep_ms_calls = [call(300), call(200), call(200)]
        utime.sleep_ms.assert_has_calls(sleep_ms_calls)
        self.assertEqual(utime.sleep_ms.call_count, 3)

    def test_writeAndReadline_return_bytes(self):
        UART.any = MagicMock(return_value=7)
        UART.readline = MagicMock(return_value=b"OK 00\r\n")
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline("SKTEST 00", "OK")
        self.assertEqual(response, ["OK 00"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(500)

    def test_writeAndReadline_inconsistent_response(self):
        UART.any = MagicMock(return_value=7)
        UART.readline = MagicMock()
        UART.readline.side_effect = [None, "OK 00\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline("SKTEST 00", "OK")
        self.assertEqual(response, ["OK 00"])
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(500)

    def test_writeAndReadline_without_crlf(self):
        UART.any = MagicMock(return_value=7)
        UART.readline = MagicMock()
        UART.readline.side_effect = [None, "OK 00\r\n"]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        response = client._writeAndReadline("SKTEST 00", "OK", auto_crlf = False)
        self.assertEqual(response, ["OK 00"])
        UART.write.assert_called_once_with("SKTEST 00")
        utime.sleep_ms.assert_called_once_with(500)

    def test_writeAndReadline_read_timeout_no_response(self):
        UART.any = MagicMock(return_value=0)
        UART.readline = MagicMock(return_value=None)
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.ReadTimeoutError) as cm:
            client._writeAndReadline(
                "SKTEST 00",
                "OK",
                max_retry = 2,
                pre_wait = 300,
                retry_wait = 200
            )
        self.assertIn("SKTEST", str(cm.exception))
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        self.assertEqual(UART.any.call_count, 3)
        sleep_ms_calls = [call(300), call(200), call(200)]
        utime.sleep_ms.assert_has_calls(sleep_ms_calls)
        self.assertEqual(utime.sleep_ms.call_count, 3)

    def test_writeAndReadline_read_timeout_break_words_not_included(self):
        UART.any = MagicMock()
        UART.any.side_effect = [6, 0, 0, 0]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["TEST\r\n", None]
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.ReadTimeoutError) as cm:
            client._writeAndReadline(
                "SKTEST 00",
                "OK",
                max_retry = 2,
                pre_wait = 300,
                retry_wait = 200
            )
        self.assertIn("SKTEST", str(cm.exception))
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        sleep_ms_calls = [call(300), call(200), call(200)]
        utime.sleep_ms.assert_has_calls(sleep_ms_calls)
        self.assertEqual(utime.sleep_ms.call_count, 3)

    def test_writeAndReadline_read_timeout_when_infinite_loop(self):
        UART.any = MagicMock(return_value=1)
        UART.readline = MagicMock(return_value=None)
        UART.write = MagicMock()
        utime.sleep_ms = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        utime.sleep_ms.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.ReadTimeoutError) as cm:
            client._writeAndReadline(
                "SKTEST 00",
                "OK",
                max_retry = 2,
                pre_wait = 300,
                retry_wait = 200
            )
        self.assertIn("SKTEST", str(cm.exception))
        UART.write.assert_called_once_with("SKTEST 00\r\n")
        utime.sleep_ms.assert_called_once_with(300)
        self.assertEqual(UART.readline.call_count, 200)

    def test_sendUDPData(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        data = b"\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\x80\x00"
        response = [
            "SKSENDTO 1 {} 0E1A 1 000E \r\n".format(ip_address),
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0012 1081000102880105FF017201E704000003E8\r\n".format(ip_address, mac_address)
        ]

        UART.any = MagicMock()
        side_effect = []
        for line in response:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = response
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        actual_response = client._sendUDPData(ip_address, data)
        expected_response = list(map(lambda line: line.rstrip(), response))
        self.assertEqual(actual_response, expected_response)
        expected_command = (
            b"SKSENDTO 1 " +
            ip_address.encode("utf-8") +
            b" 0E1A 1 000E " +
            data
        )
        UART.write.assert_called_once_with(expected_command)

    def test_sendUDPData_with_break_words(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        data = b"\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\x80\x00"
        response = [
            "SKSENDTO 1 {} 0E1A 1 000E \r\n".format(ip_address),
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0012 1081000102880105FF017201E704000003E8\r\n".format(ip_address, mac_address),
            "EVENT 21\r\n"
        ]

        UART.any = MagicMock()
        side_effect = []
        for line in response:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = response
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        expected_leading_frame = "1081000102880105FF01"
        actual_response = client._sendUDPData(ip_address, data, (expected_leading_frame, expected_leading_frame.lower()))
        expected_response = list(map(lambda line: line.rstrip(), response[0:-1]))
        self.assertEqual(actual_response, expected_response)
        expected_command = (
            b"SKSENDTO 1 " +
            ip_address.encode("utf-8") +
            b" 0E1A 1 000E " +
            data
        )
        UART.write.assert_called_once_with(expected_command)

    def test_extractUDPData(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        event = "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0012 1081000102880105FF017201E704000003E8".format(ip_address, mac_address)

        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        actual_data = client._extractUDPData(event)
        expected_data = "1081000102880105FF017201E704000003E8"
        self.assertEqual(actual_data, expected_data)

    def test_extractUDPData_unexpected_event(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(ValueError):
            client._extractUDPData("OK 00")

    def test_findFrameFromResponseEvents(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        data = b"\x10\x81\x01\xFE\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00"
        events = [
            "SKSENDTO 1 {} 0E1A 1 000E ".format(ip_address),
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0012 108100000EF0010EF0017301D50400123456".format(ip_address, mac_address),
            "EVENT 21 {} 00".format(ip_address),
            "OK",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0012 108101FE02880105FF017201E704000003E8".format(ip_address, mac_address)
        ]
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        actual = client._findFrameFromResponseEvents(events, data)
        expected = {
            "EHD1": 0x10,
            "EHD2": 0x81,
            "TID" : 0x01FE,
            "SEOJ": 0x028801,
            "DEOJ": 0x05FF01,
            "ESV" : 0x72,
            "OPC" : 0x01,
            "EPC" : 0xE7,
            "PDC" : 0x04,
            "EDT" : "000003E8"
        }
        self.assertEqual(actual, expected)

    def test_createEchonetLiteFrame(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = client._createEchonetLiteFrame(epc = 0x80)
        self.assertIsInstance(frame, bytes)
        expected = b'\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x62\x01\x80\x00'
        self.assertEqual(frame, expected)

    def test_createEchonetLiteFrame_set_tid(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = client._createEchonetLiteFrame(epc = 0xE7, tid = 0x01FF)
        self.assertIsInstance(frame, bytes)
        expected = b'\x10\x81\x01\xFF\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00'
        self.assertEqual(frame, expected)

    def test_createEchonetLiteFrame_epc_overflow(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(OverflowError):
            client._createEchonetLiteFrame(epc = 0x0100)

    def test_createEchonetLiteFrame_tid_overflow(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(OverflowError):
            client._createEchonetLiteFrame(epc = 0xE7, tid = 0x01FFFF)

    def test_createEchonetLiteFrame_set_c(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = client._createEchonetLiteFrame(epc = 0xE5, esv = 0x61, edt = b'\x63')
        self.assertIsInstance(frame, bytes)
        expected = b'\x10\x81\x00\x01\x05\xFF\x01\x02\x88\x01\x61\x01\xE5\x01\x63'
        self.assertEqual(frame, expected)

    def test_createExpectedEchonetLiteResponseLeadingFrame(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = b'\x10\x81\x01\xFE\x05\xFF\x01\x02\x88\x01\x62\x01\xE7\x00'
        actual = client._createExpectedEchonetLiteResponseLeadingFrame(frame)
        expected = "108101FE02880105FF01"
        self.assertEqual(actual, expected)

    def test_parseEchonetLiteFrame(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = "1081000102880105FF017201E704000003E8"
        data = client._parseEchonetLiteFrame(frame)
        expected = {
            "EHD1": 0x10,
            "EHD2": 0x81,
            "TID" : 0x0001,
            "SEOJ": 0x028801,
            "DEOJ": 0x05FF01,
            "ESV" : 0x72,
            "OPC" : 0x01,
            "EPC" : 0xE7,
            "PDC" : 0x04,
            "EDT" : "000003E8"
        }
        self.assertEqual(data, expected)

    def test_parseEchonetLiteFrame_too_short(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = "1081000102880105FF017201E7"
        with self.assertRaises(ValueError) as cm:
            client._parseEchonetLiteFrame(frame)
        self.assertEqual(str(cm.exception), "Frame data too short.")

    def test_parseEchonetLiteFrame_no_edt(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        frame = "1081000102880105FF017201E700"
        data = client._parseEchonetLiteFrame(frame)
        expected = {
            "EHD1": 0x10,
            "EHD2": 0x81,
            "TID" : 0x0001,
            "SEOJ": 0x028801,
            "DEOJ": 0x05FF01,
            "ESV" : 0x72,
            "OPC" : 0x01,
            "EPC" : 0xE7,
            "PDC" : 0x00,
            "EDT" : None
        }
        self.assertEqual(data, expected)

    def test_convertUnsignedToSigned(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertEqual(client._convertUnsignedToSigned(0, 16), 0)
        self.assertEqual(client._convertUnsignedToSigned(0x8000, 16), -32768)
        self.assertEqual(client._convertUnsignedToSigned(0x8001, 16), -32767)
        self.assertEqual(client._convertUnsignedToSigned(0x7FFF, 16), 32767)
        self.assertEqual(client._convertUnsignedToSigned(0xFFFF, 16), -1)
        self.assertEqual(client._convertUnsignedToSigned(0x80000000, 32), -2147483648)
        self.assertEqual(client._convertUnsignedToSigned(0x80000001, 32), -2147483647)
        self.assertEqual(client._convertUnsignedToSigned(0x7FFFFFFF, 32), 2147483647)
        self.assertEqual(client._convertUnsignedToSigned(0xFFFFFFFF, 32), -1)

    def test_nextTransactionId(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertEqual(client._nextTransactionId(), 1)
        self.assertEqual(client._nextTransactionId(), 2)
        self.assertEqual(client._nextTransactionId(), 3)

        client._tid = 0xFFFE
        self.assertEqual(client._nextTransactionId(), 65535)
        self.assertEqual(client._nextTransactionId(), 1)

    def test_clearBuffer(self):
        UART.any = MagicMock(return_value=0)
        UART.readline = MagicMock(return_value="")
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.clearBuffer()
        UART.write.assert_called_once_with("\r\n")

    def test_isDeviceAvailable(self):
        UART.any = MagicMock()
        UART.any.side_effect = [8, 77, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = [
            "SKINFO\r\n",
            "EINFO {0} {1} 21 FFFF FFFE\r\n".format(self.createIPv6Address(), self.createMacAddress()),
            "OK\r\n"
        ]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertTrue(client.isDeviceAvailable())
        UART.write.assert_called_once_with("SKINFO\r\n")

    def test_isDeviceAvailable_unavailable(self):
        UART.any = MagicMock(return_value=0)
        UART.readline = MagicMock()
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertFalse(client.isDeviceAvailable())
        UART.write.assert_called_once_with("SKINFO\r\n")

    def test_execGetInfo(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        UART.any = MagicMock()
        UART.any.side_effect = [8, 77, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = [
            "SKINFO\r\n",
            "EINFO {0} {1} 21 FFFF FFFE\r\n".format(ip_address, mac_address),
            "OK\r\n"
        ]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        actual = client.execGetInfo()
        expected = {
            "ip_address": ip_address,
            "mac_address": mac_address,
            "channel": "21",
            "pan_id": "FFFF",
        }
        self.assertEqual(actual ,expected)
        UART.write.assert_called_once_with("SKINFO\r\n")

    def test_execGetInfo_unexpected_response(self):
        UART.any = MagicMock()
        UART.any.side_effect = [8, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKINFO\r\n", "OK\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.UnexpectedResponseError) as cm:
            client.execGetInfo()
        self.assertEqual(str(cm.exception), "SKINFO returns unexpected response.")
        UART.write.assert_called_once_with("SKINFO\r\n")

    def test_execEchoBack_on(self):
        UART.any = MagicMock()
        UART.any.side_effect = [4, 0]
        UART.readline = MagicMock(return_value="OK\r\n")
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execEchoBack(True)
        UART.write.assert_called_once_with("SKSREG SFE 1\r\n")

    def test_execEchoBack_off(self):
        UART.any = MagicMock()
        UART.any.side_effect = [4, 0]
        UART.readline = MagicMock(return_value="OK\r\n")
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execEchoBack(False)
        UART.write.assert_called_once_with("SKSREG SFE 0\r\n")

    def test_execSetAsciiMode_binary_to_ascii(self):
        UART.any = MagicMock()
        UART.any.side_effect = [7, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["OK 00\r\n", "OK\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertTrue(client.execSetAsciiMode())
        write_calls = [
            call("ROPT\r\n"),
            call("WOPT 01\r\n")
        ]
        UART.write.assert_has_calls(write_calls)

    def test_execSetAsciiMode_no_change(self):
        UART.any = MagicMock(return_value=7)
        UART.readline = MagicMock(return_value="OK 01\r\n")
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertFalse(client.execSetAsciiMode())
        UART.write.assert_called_once_with("ROPT\r\n")

    def test_execTerminateSession(self):
        UART.any = MagicMock(return_value=4)
        UART.readline = MagicMock(return_value="OK\r\n")
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertTrue(client.execTerminateSession())
        UART.write.assert_called_once_with("SKTERM\r\n")

    def test_execTerminateSession_not_established(self):
        UART.any = MagicMock(return_value=11)
        UART.readline = MagicMock(return_value="FAIL ER10\r\n")
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        self.assertFalse(client.execTerminateSession())
        UART.write.assert_called_once_with("SKTERM\r\n")

    def test_execSetPwd(self):
        password = "0123456789AB"
        UART.any = MagicMock()
        UART.any.side_effect = [25, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKSETPWD C " + password + "\r\n", "OK\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execSetPwd(password)
        UART.write.assert_called_once_with("SKSETPWD C " + password + "\r\n")

    def test_execSetPwd_password_too_short(self):
        password = "0123456789A"
        UART.any = MagicMock()
        UART.readline = MagicMock()
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(ValueError) as cm:
            client.execSetPwd(password)
        self.assertEqual(str(cm.exception), "Password length must be 12.")
        UART.write.assert_not_called()

    def test_execSetRbId(self):
        rbid = "012345678901234567890123456789AB"
        UART.any = MagicMock()
        UART.any.side_effect = [44, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKSETRBID " + rbid + "\r\n", "OK\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execSetRbId(rbid)
        UART.write.assert_called_once_with("SKSETRBID " + rbid + "\r\n")

    def test_execSetRbId_rbid_too_long(self):
        rbid = "012345678901234567890123456789ABC"
        UART.any = MagicMock()
        UART.readline = MagicMock()
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(ValueError) as cm:
            client.execSetRbId(rbid)
        self.assertEqual(str(cm.exception), "Route-B ID length must be 32.")
        UART.write.assert_not_called()

    def test_execScan(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "SKSCAN 2 FFFFFFFF 6\r\n",
            "OK\r\n",
            "EVENT 20 {0}\r\n".format(ip_address),
            "EPANDESC\r\n",
            "  Channel:21\r\n",
            "  Channel Page:09\r\n",
            "  Pan ID:8888\r\n",
            "  Addr:{0}\r\n".format(mac_address),
            "  LQI:E1\r\n",
            "  PairID:01234567B\r\n",
            "EVENT 22 {0}\r\n".format(ip_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        for _ in range(5):
            side_effect.insert(2, 0)
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        actual_params = client.execScan()
        expected_params = {
            "Channel": "21",
            "Channel Page": "09",
            "Pan ID": "8888",
            "Addr": mac_address,
            "LQI": "E1",
            "PairID": "01234567B",
        }
        self.assertEqual(actual_params, expected_params)
        UART.write.assert_called_once_with("SKSCAN 2 FFFFFFFF 6\r\n")

    def test_execScan_event_first(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 22 {0}\r\n".format(ip_address),
            "SKSCAN 2 FFFFFFFF 6\r\n",
            "OK\r\n",
            "EVENT 20 {0}\r\n".format(ip_address),
            "EPANDESC\r\n",
            "  Channel:21\r\n",
            "  Channel Page:09\r\n",
            "  Pan ID:8888\r\n",
            "  Addr:{0}\r\n".format(mac_address),
            "  LQI:E1\r\n",
            "  PairID:01234567B\r\n"
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        actual_params = client.execScan()
        expected_params = {
            "Channel": "21",
            "Channel Page": "09",
            "Pan ID": "8888",
            "Addr": mac_address,
            "LQI": "E1",
            "PairID": "01234567B",
        }
        self.assertEqual(actual_params, expected_params)
        UART.write.assert_called_once_with("SKSCAN 2 FFFFFFFF 6\r\n")

    def test_execScan_read_timeout_error(self):
        responses = [
            "SKSCAN 2 FFFFFFFF 6\r\n",
            "OK\r\n",
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.ReadTimeoutError) as cm:
            client.execScan()
        self.assertIn("SKSCAN", str(cm.exception))
        UART.write.assert_called_once_with("SKSCAN 2 FFFFFFFF 6\r\n")

    def test_execSetChannel(self):
        channel = "21"
        UART.any = MagicMock()
        UART.any.side_effect = [14, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKSREG S2 21\r\n", "OK\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execSetChannel(channel)
        UART.write.assert_called_once_with("SKSREG S2 " + channel + "\r\n")

    def test_execSetPanId(self):
        pan_id = "FEDC"
        UART.any = MagicMock()
        UART.any.side_effect = [16, 4]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKSREG S3 FEDC\r\n", "OK\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execSetPanId(pan_id)
        UART.write.assert_called_once_with("SKSREG S3 " + pan_id + "\r\n")

    def test_execConvertAddress(self):
        mac_address = self.createMacAddress()
        converted_ip_address = self.createIPv6Address()
        UART.any = MagicMock()
        UART.any.side_effect = [25, 41]
        UART.readline = MagicMock()
        UART.readline.side_effect = ["SKLL64 " + mac_address + "\r\n", converted_ip_address + "\r\n"]
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        ip_address = client.execConvertAddress(mac_address)
        self.assertEqual(ip_address, converted_ip_address)
        UART.write.assert_called_once_with("SKLL64 " + mac_address + "\r\n")

    def test_execJoin(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {0} 00\r\n".format(ip_address),
            "ERXUDP {0} {0} 0001 0002 {1} 0 000A 00010203040506070809\r\n".format(ip_address, mac_address),
            "EVENT 21 {0} 00\r\n".format(ip_address),
            "ERXUDP {0} {0} 02CC 02CC {1} 0 000A 00010203040506070809\r\n".format(ip_address, mac_address),
            "EVENT 21 {0} 00\r\n".format(ip_address),
            "EVENT 25 {0}\r\n".format(ip_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.execJoin(ip_address)
        UART.write.assert_called_once_with("SKJOIN " + ip_address + "\r\n")
        self.assertEqual(client._ip_address, ip_address)

    def test_execJoin_connection_failed(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {0} 00\r\n".format(ip_address),
            "ERXUDP {0} {0} 0001 0002 {1} 0 000A 00010203040506070809\r\n".format(ip_address, mac_address),
            "EVENT 21 {0} 00\r\n".format(ip_address),
            "ERXUDP {0} {0} 02CC 02CC {1} 0 000A 00010203040506070809\r\n".format(ip_address, mac_address),
            "EVENT 21 {0} 00\r\n".format(ip_address),
            "EVENT 24 {0}\r\n".format(ip_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.ConnectionError) as cm:
            client.execJoin(ip_address)
        self.assertEqual(str(cm.exception), "Connection failed.")
        UART.write.assert_called_once_with("SKJOIN " + ip_address + "\r\n")
        self.assertIsNone(client._ip_address)

    def test_execGetStatus_on(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201800130\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertTrue(client.execGetStatus())

    def test_execGetStatus_off(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201800131\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertFalse(client.execGetStatus())

    def test_execGetStatus_unknown(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201800100\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertIsNone(client.execGetStatus())

    def test_execGetStatus_exception_has_correct_command_head(self):
        ip_address = self.createIPv6Address()
        UART.any = MagicMock(return_value=0)
        UART.readline = MagicMock()
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        with self.assertRaises(wisun.ReadTimeoutError) as cm:
            client.execGetStatus()
        self.assertIn("(SKSENDTO)", str(cm.exception))

    def test_execGetStatus_undefined_address(self):
        UART.any = MagicMock()
        UART.readline = MagicMock()
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        with self.assertRaises(wisun.UndefinedAddressError) as cm:
            client.execGetStatus()
        self.assertEqual(str(cm.exception), "IPv6 address must not be None.")

    def test_execGetFactor_min(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201D30400000000\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetFactor(), 0)

    def test_execGetFactor_max(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201D304000F423F\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetFactor(), 999999)

    def test_execGetSignificantFigures_min(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201D70101\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetSignificantFigures(), 1)

    def test_execGetSignificantFigures_max(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201D70108\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetSignificantFigures(), 8)

    def test_execGetIntegralPowerConsumption_min(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E00400000000\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumption(), 0)

    def test_execGetIntegralPowerConsumption_max(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E00405F5E0FF\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumption(), 99999999)

    def test_execGetIntegralPowerConsumption_max_with_calc_params(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E00405F5E0FF\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        client.setPowerConsumptionCalcParams(factor=1, unit=0.1)
        self.assertAlmostEqual(client.execGetIntegralPowerConsumption(), 9999999.9)

    def test_execGetIntegralPowerConsumptionUnit_1k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E10100\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumptionUnit(), 1)

    def test_execGetIntegralPowerConsumptionUnit_0_1k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E10101\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertAlmostEqual(client.execGetIntegralPowerConsumptionUnit(), 0.1)

    def test_execGetIntegralPowerConsumptionUnit_0_01k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E10102\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertAlmostEqual(client.execGetIntegralPowerConsumptionUnit(), 0.01)

    def test_execGetIntegralPowerConsumptionUnit_0_001k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E10103\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertAlmostEqual(client.execGetIntegralPowerConsumptionUnit(), 0.001)

    def test_execGetIntegralPowerConsumptionUnit_0_0001k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E10104\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertAlmostEqual(client.execGetIntegralPowerConsumptionUnit(), 0.0001)

    def test_execGetIntegralPowerConsumptionUnit_10k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E1010A\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumptionUnit(), 10)

    def test_execGetIntegralPowerConsumptionUnit_100k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E1010B\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumptionUnit(), 100)

    def test_execGetIntegralPowerConsumptionUnit_1000k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E1010C\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumptionUnit(), 1000)

    def test_execGetIntegralPowerConsumptionUnit_10000k(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E1010D\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetIntegralPowerConsumptionUnit(), 10000)

    def test_execGetIntegralPowerConsumptionUnit_undefined(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E101FF\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertIsNone(client.execGetIntegralPowerConsumptionUnit())

    def test_execGetCurrentPowerConsumption_min(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E70480000001\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetCurrentPowerConsumption(), -2147483647)

    def test_execGetCurrentPowerConsumption_max(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E7047FFFFFFD\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetCurrentPowerConsumption(), 2147483645)

    def test_execGetCurrentAmpere_r_min_t_max(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E80480017FFD\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetCurrentAmpere(), (-32767, 32765))

    def test_execGetCurrentAmpere_r_max_t_mmin(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E8047FFD8001\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetCurrentAmpere(), (32765, -32767))

    def test_execGetCurrentAmpere_t_undefined(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E80400007FFE\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetCurrentAmpere(), (0, None))

    def test_execGetLast30MinutesPowerConsumption(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0019 1081000102880105FF017201EA0B270F0C01173B1E05F5E0FF\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        actual = client.execGetLast30MinutesPowerConsumption()
        expected = {
            "year": 9999,
            "mon": 12,
            "mday": 1,
            "hour": 23,
            "min": 59,
            "sec": 30,
            "power": 99999999
        }
        self.assertEqual(actual, expected)

    def test_execGetLast30MinutesPowerConsumption_with_calc_params(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 0019 1081000102880105FF017201EA0B270F0C01173B1E05F5E0FF\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        client.setPowerConsumptionCalcParams(factor=1, unit=0.1)
        actual = client.execGetLast30MinutesPowerConsumption()
        expected = {
            "year": 9999,
            "mon": 12,
            "mday": 1,
            "hour": 23,
            "min": 59,
            "sec": 30,
            "power": 9999999.9
        }
        self.assertEqual(actual, expected)

    def test_execSetTargetDayForHistory(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000E 1081000102880105FF017201E500\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertTrue(client.execSetTargetDayForHistory(99))

    def test_execGetTargetDayForHistory(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 000F 1081000102880105FF017201E50163\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        self.assertEqual(client.execGetTargetDayForHistory(), 99)

    def test_execGetPowerConsumptionHistory(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 00D0 1081000102880105FF017201E2C200010010F4470010F4480010F4490010F44A0010F44B0010F44C0010F44D0010F44E0010F44F0010F4500010F4510010F4520010F4530010F4540010F4550010F4560010F4570010F4580010F4590010F45A0010F45B0010F45C0010F45D0010F45E0010F45F0010F4600010F4610010F4620010F4630010F4640010F4650010F4660010F4670010F4680010F4690010F46A0010F46B0010F46C0010F46D0010F46E0010F46F0010F4700010F4710010F4720010F4730010F4740010F4750010F476\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        actual = client.execGetPowerConsumptionHistory()
        expected = {
            "day": 1,
            "powers": []
        }
        for i in range(48):
            expected["powers"].append(1111111 + i)
        self.assertEqual(actual, expected)

    def test_execGetPowerConsumptionHistory_with_nr(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 00D0 1081000102880105FF017201E2C200010010F4470010F4480010F449FFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFE\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        actual = client.execGetPowerConsumptionHistory()
        expected = {
            "day": 1,
            "powers": []
        }
        for i in range(3):
            expected["powers"].append(1111111 + i)
        expected["powers"] += [None] * 45
        self.assertEqual(actual, expected)

    def test_execGetPowerConsumptionHistory_with_calc_params(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 00D0 1081000102880105FF017201E2C200010010F4470010F4480010F4490010F44A0010F44B0010F44C0010F44D0010F44E0010F44F0010F4500010F4510010F4520010F4530010F4540010F4550010F4560010F4570010F4580010F4590010F45A0010F45B0010F45C0010F45D0010F45E0010F45F0010F4600010F4610010F4620010F4630010F4640010F4650010F4660010F4670010F4680010F4690010F46A0010F46B0010F46C0010F46D0010F46E0010F46F0010F4700010F4710010F4720010F4730010F4740010F4750010F476\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        client.setPowerConsumptionCalcParams(factor=1, unit=0.1)
        actual = client.execGetPowerConsumptionHistory()
        expected = {
            "day": 1,
            "powers": []
        }
        for i in range(48):
            expected["powers"].append(111111.1 + i / 10)
        self.assertEqual(actual, expected)

    def test_execGetPowerConsumptionHistory_with_nr_and_calc_params(self):
        ip_address = self.createIPv6Address()
        mac_address = self.createMacAddress()
        responses = [
            "EVENT 21 {} 00\r\n".format(ip_address),
            "OK\r\n",
            "ERXUDP {0} {0} 0E1A 0E1A {1} 1 00D0 1081000102880105FF017201E2C200010010F4470010F4480010F449FFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFEFFFFFFFE\r\n".format(ip_address, mac_address)
        ]
        UART.any = MagicMock()
        side_effect = []
        for line in responses:
            side_effect.append(len(line))
        side_effect += [0] * 100
        UART.any.side_effect = side_effect
        UART.readline = MagicMock()
        UART.readline.side_effect = responses
        UART.write = MagicMock()

        UART.any.reset_mock()
        UART.readline.reset_mock()
        UART.write.reset_mock()
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client._ip_address = ip_address
        client.setPowerConsumptionCalcParams(factor=1, unit=0.1)
        actual = client.execGetPowerConsumptionHistory()
        expected = {
            "day": 1,
            "powers": []
        }
        for i in range(3):
            expected["powers"].append(111111.1 + i / 10)
        expected["powers"] += [None] * 45
        self.assertEqual(actual, expected)

    def test_getMaxIntegralPowerConsumption(self):
        client = wisun.BP35A1Client(uart=UART, utime=utime, logging=logging)
        client.setPowerConsumptionCalcParams(factor=1, unit=0.1)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(8), 9999999.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(7), 999999.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(6), 99999.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(5), 9999.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(4), 999.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(3), 99.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(2), 9.9)
        self.assertAlmostEqual(client.getMaxIntegralPowerConsumption(1), .9)
