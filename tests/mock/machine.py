class UART:
    def __init__(self, id, **kwargs):
        self._id = id
        self._kwargs = kwargs

    def init(self, baudrate=9600, bits=8, parity=None, stop=1, **kwargs):
        self._baudrate = baudrate
        self._bits = bits
        self._parity = parity
        self._stop = stop
        self._init_kwargs = kwargs

    def deinit(self):
        pass

    def any(self):
        return 0

    def read(self, nbytes = -1):
        return None

    def readline(self):
        return None

    def write(buf):
        return len(buf)
