# main.py — NTP daily sync + monotonic; Stockholm time; Greek-summer light
# Requires on CIRCUITPY/lib:
#   adafruit_ntp.mpy


import os
import math
import time
import board
import pwmio
import wifi
import socketpool
import adafruit_ntp

# -----------------------------
# Hardware: single PWM channel
# -----------------------------
LED_PIN = board.GP15
PWM_FREQ = 1000
_led = pwmio.PWMOut(LED_PIN, frequency=PWM_FREQ, duty_cycle=0)

def set_led_brightness(level: float, gamma: float = 2.2) -> None:
    # level: 0..1, gamma-compensated
    if level <= 0.0:
        _led.duty_cycle = 0
        return
    if level >= 1.0:
        _led.duty_cycle = 65535
        return
    _led.duty_cycle = int((level ** gamma) * 65535 + 0.5)

# -----------------------------
# Wi-Fi
# -----------------------------
def wifi_connect() -> socketpool.SocketPool:
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    pwd  = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    if not ssid:
        raise RuntimeError("Missing Wi-Fi settings.toml (CIRCUITPY_WIFI_SSID/PASSWORD).")
    print("Wi-Fi: connecting to", ssid)
    wifi.radio.connect(ssid, pwd)
    print("Wi-Fi: connected, IP:", wifi.radio.ipv4_address)
    return socketpool.SocketPool(wifi.radio)

# -----------------------------
# Time keeping: NTP + monotonic
# -----------------------------
SYNC_INTERVAL_S = 24 * 60 * 60  # once/day
NTP_SERVER = "0.adafruit.pool.ntp.org"

class TimeSync:
    """
    Keep UTC epoch seconds. Sync rarely via NTP, then advance using time.monotonic().
    No adafruit_datetime usage (avoids time.gmtime).
    """
    def __init__(self, pool: socketpool.SocketPool):
        self.ntp = adafruit_ntp.NTP(pool, server=NTP_SERVER, tz_offset=0)  # UTC
        self._utc_epoch = 0
        self._mono_ref = 0.0
        self._next_sync = 0.0

    def sync_now(self) -> None:
        # NTP gives a UTC struct_time; convert to epoch using time.mktime.
        # CircuitPython's time.mktime exists; there is no timezone concept, so it's fine.
        st = self.ntp.datetime  # time.struct_time in UTC
        self._utc_epoch = int(time.mktime(st))
        self._mono_ref = time.monotonic()
        self._next_sync = self._mono_ref + SYNC_INTERVAL_S
        print("NTP sync OK: %04d-%02d-%02dT%02d:%02d:%02dZ" %
              (st.tm_year, st.tm_mon, st.tm_mday, st.tm_hour, st.tm_min, st.tm_sec))

    def maybe_sync(self) -> None:
        if time.monotonic() >= self._next_sync:
            try:
                self.sync_now()
            except Exception as e:
                print("NTP sync failed:", e)
                # retry later; keep running on monotonic time
                self._next_sync = time.monotonic() + 3600

    def utc_now(self) -> int:
        if self._utc_epoch == 0:
            self.sync_now()
        return int(self._utc_epoch + (time.monotonic() - self._mono_ref))

# -----------------------------
# Stockholm (CET/CEST) DST math
# -----------------------------
def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def _days_in_month(y: int, m: int) -> int:
    if m == 2:
        return 29 if _is_leap(y) else 28
    return [31, -1, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m-1]

def _weekday_sun0(y: int, m: int, d: int) -> int:
    # Sakamoto’s algorithm — returns 0=Sunday..6=Saturday
    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if m < 3:
        y -= 1
    return (y + y//4 - y//100 + y//400 + t[m-1] + d) % 7

def _last_sunday_day(y: int, m: int) -> int:
    last = _days_in_month(y, m)
    w = _weekday_sun0(y, m, last)  # 0=Sun
    return last - w  # go back w days to Sunday

def stockholm_utc_offset_seconds_from_utc_struct(utc_st: time.struct_time) -> int:
    """
    EU rule: DST from last Sunday in March 01:00 UTC to last Sunday in October 01:00 UTC.
    CET = UTC+1 (winter), CEST = UTC+2 (summer).
    """
    y = utc_st.tm_year
    start_day = _last_sunday_day(y, 3)
    end_day   = _last_sunday_day(y, 10)

    now = (utc_st.tm_mon, utc_st.tm_mday, utc_st.tm_hour, utc_st.tm_min, utc_st.tm_sec)
    start = (3, start_day, 1, 0, 0)
    end   = (10, end_day, 1, 0, 0)

    in_dst = (now >= start) and (now < end)
    return 7200 if in_dst else 3600

# -----------------------------
# Greek-summer brightness curve
# -----------------------------
def greek_summer_brightness(local_st: time.struct_time) -> float:
    """
    Brighten as if Greece in summer, but keyed to Stockholm local clock.
    Day window: 06:00–20:30, smooth sine peaking at midday.
    """
    seconds = local_st.tm_hour * 3600 + local_st.tm_min * 60 + local_st.tm_sec
    SR = 6 * 3600                    # 06:00
    SS = 20 * 3600 + 30 * 60         # 20:30
    if seconds <= SR or seconds >= SS:
        return 0.0
    span = SS - SR
    x = (seconds - SR) / span        # 0..1 across daylight window
    return math.sin(math.pi * x)     # 0 at edges, 1 at solar noon

# -----------------------------
# Main
# -----------------------------
def main():
    pool = wifi_connect()

    ts = TimeSync(pool)
    ts.sync_now()

    last_print = 0.0
    while True:
        ts.maybe_sync()

        utc_epoch = ts.utc_now()
        utc_st = time.localtime(utc_epoch)  # treat as UTC struct_time

        offset = stockholm_utc_offset_seconds_from_utc_struct(utc_st)
        local_st = time.localtime(utc_epoch + offset)

        b = greek_summer_brightness(local_st)
        set_led_brightness(b)

        now = time.monotonic()
        if now - last_print >= 10:
            # ISO-like local timestamp
            print(
                "%04d-%02d-%02dT%02d:%02d:%02d (Stockholm) | offset:%4ds | Brightness: %.3f" %
                (local_st.tm_year, local_st.tm_mon, local_st.tm_mday,
                 local_st.tm_hour, local_st.tm_min, local_st.tm_sec,
                 offset, b)
            )
            last_print = now

        time.sleep(0.05)  # smooth updates

if __name__ == "__main__":
    main()

