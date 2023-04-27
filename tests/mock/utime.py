from datetime import datetime, timezone

timestamp = None

EPOCH_OFFSET = 946684800  # Unix epoch の 2000/1/1 00:00:00 ← 組み込み機器のエポック

def localtime(secs = None):
    if timestamp is None and secs is None:
        return (2000, 1, 2, 3, 4, 5, 6, 2)

    t = timestamp
    if secs is not None:
        t = secs
    dt = datetime.fromtimestamp(t + EPOCH_OFFSET, timezone.utc)
    st = dt.timetuple()
    return (
        st.tm_year,
        st.tm_mon,
        st.tm_mday,
        st.tm_hour,
        st.tm_min,
        st.tm_sec,
        st.tm_wday,
        st.tm_yday
    )

def mktime(t):
    if timestamp is None:
        return 12345

    if not isinstance(t, tuple):
        raise TypeError("Tuple argument required")
    if len(t) != 8:
        raise TypeError("illegal tuple argument")
    dt = datetime(
        t[0],  # year
        t[1],  # month
        t[2],  # mday
        t[3],  # hour
        t[4],  # minute
        t[5],  # second
        tzinfo=timezone.utc
    )
    return int(dt.timestamp() - EPOCH_OFFSET)

def sleep(seconds):
    pass

def sleep_ms(ms):
    pass

def time():
    if timestamp is None:
        return 12345

    return timestamp
