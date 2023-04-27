import unittest
from unittest.mock import MagicMock, call
from mock import utime
from wmlogging import Logger as logging

class TestLogger(unittest.TestCase):
    def test_log_default(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output
        )
        logging.log(logging.DEBUG, "debug message")
        logging.log(logging.INFO, "info message")
        logging.log(logging.WARN, "warn message")
        logging.log(logging.WARNING, "warning message")
        logging.log(logging.ERROR, "error message")
        logging.log(logging.FATAL, "fatal message")
        logging.log(logging.CRITICAL, "critical message")

        expected = [
            call("WARNING: warn message"),
            call("WARNING: warning message"),
            call("ERROR: error message"),
            call("CRITICAL: fatal message"),
            call("CRITICAL: critical message")
        ]
        output.assert_has_calls(expected)
        self.assertEqual(output.call_count, len(expected))

    def test_log_debug_output(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.DEBUG
        )
        logging.log(logging.DEBUG, "debug message")
        logging.log(logging.INFO, "info message")
        logging.log(logging.WARN, "warn message")
        logging.log(logging.WARNING, "warning message")
        logging.log(logging.ERROR, "error message")
        logging.log(logging.FATAL, "fatal message")
        logging.log(logging.CRITICAL, "critical message")

        expected = [
            call("DEBUG: debug message"),
            call("INFO: info message"),
            call("WARNING: warn message"),
            call("WARNING: warning message"),
            call("ERROR: error message"),
            call("CRITICAL: fatal message"),
            call("CRITICAL: critical message")
        ]
        output.assert_has_calls(expected)
        self.assertEqual(output.call_count, len(expected))

    def test_log_info_output(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.INFO
        )
        logging.log(logging.DEBUG, "debug message")
        logging.log(logging.INFO, "info message")
        logging.log(logging.WARN, "warn message")
        logging.log(logging.WARNING, "warning message")
        logging.log(logging.ERROR, "error message")
        logging.log(logging.FATAL, "fatal message")
        logging.log(logging.CRITICAL, "critical message")

        expected = [
            call("INFO: info message"),
            call("WARNING: warn message"),
            call("WARNING: warning message"),
            call("ERROR: error message"),
            call("CRITICAL: fatal message"),
            call("CRITICAL: critical message")
        ]
        output.assert_has_calls(expected)
        self.assertEqual(output.call_count, len(expected))

    def test_log_warn_output(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.WARNING
        )
        logging.log(logging.DEBUG, "debug message")
        logging.log(logging.INFO, "info message")
        logging.log(logging.WARN, "warn message")
        logging.log(logging.WARNING, "warning message")
        logging.log(logging.ERROR, "error message")
        logging.log(logging.FATAL, "fatal message")
        logging.log(logging.CRITICAL, "critical message")

        expected = [
            call("WARNING: warn message"),
            call("WARNING: warning message"),
            call("ERROR: error message"),
            call("CRITICAL: fatal message"),
            call("CRITICAL: critical message")
        ]
        output.assert_has_calls(expected)
        self.assertEqual(output.call_count, len(expected))

    def test_log_error_output(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.ERROR
        )
        logging.log(logging.DEBUG, "debug message")
        logging.log(logging.INFO, "info message")
        logging.log(logging.WARN, "warn message")
        logging.log(logging.WARNING, "warning message")
        logging.log(logging.ERROR, "error message")
        logging.log(logging.FATAL, "fatal message")
        logging.log(logging.CRITICAL, "critical message")

        expected = [
            call("ERROR: error message"),
            call("CRITICAL: fatal message"),
            call("CRITICAL: critical message")
        ]
        output.assert_has_calls(expected)
        self.assertEqual(output.call_count, len(expected))

    def test_log_critical_output(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.CRITICAL
        )
        logging.log(logging.DEBUG, "debug message")
        logging.log(logging.INFO, "info message")
        logging.log(logging.WARN, "warn message")
        logging.log(logging.WARNING, "warning message")
        logging.log(logging.ERROR, "error message")
        logging.log(logging.FATAL, "fatal message")
        logging.log(logging.CRITICAL, "critical message")

        expected = [
            call("CRITICAL: fatal message"),
            call("CRITICAL: critical message")
        ]
        output.assert_has_calls(expected)
        self.assertEqual(output.call_count, len(expected))

    def test_log_with_date_string(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            utime=utime
        )
        logging.log(logging.CRITICAL, "critical message")

        output.assert_called_once_with("[2000-01-02 03:04:05] CRITICAL: critical message")

    def test_basicConfig_undefined_level(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output
        )
        logging.log(999999, "unknown message")

        output.assert_called_once_with("UNKNOWN: unknown message")

    def test_debug(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.DEBUG
        )
        logging.debug("debug message")
        output.assert_called_once_with("DEBUG: debug message")

    def test_info(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.INFO
        )
        logging.info("info message")
        output.assert_called_once_with("INFO: info message")

    def test_warning(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.WARNING
        )
        logging.warning("warning message")
        output.assert_called_once_with("WARNING: warning message")

    def test_error(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.ERROR
        )
        logging.error("error message")
        output.assert_called_once_with("ERROR: error message")

    def test_ciritical(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output,
            level=logging.CRITICAL
        )
        logging.critical("critical message")
        output.assert_called_once_with("CRITICAL: critical message")

    def test_exception(self):
        output = MagicMock()
        logging.reset()
        logging.basicConfig(
            output_func=output
        )
        logging.exception(Exception("exception message"))
        output.assert_called_once_with("ERROR: <Exception> exception message")
