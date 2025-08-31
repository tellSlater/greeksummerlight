import pwmio
import board
import math
import microcontroller
from microcontroller import watchdog
from watchdog import WatchDogMode
import time
import wifi, ssl, socketpool, adafruit_requests

UTC_time_offset = 0

# Setup PWM for LED strip
led_pwm = pwmio.PWMOut(board.GP15, frequency=1000, duty_cycle=0)

def set_led_brightness(level: float):
    """level: 0.0 (off) to 1.0 (max)"""
    duty = int(level * 65535)
    led_pwm.duty_cycle = duty

def parse_utc_offset(offset_str: str) -> int:
    """
    Converts an offset string like '+02:00:00' or '-01:30:00' into seconds.
    Returns 0 if the format is invalid.
    """
    try:
        sign = -1 if offset_str.startswith("-") else 1
        parts = offset_str.strip("+-").split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        return sign * (hours * 3600 + minutes * 60 + seconds)
    except:
        return 0

def greek_summer_light(unix_time: int, stockholm_offset: str) -> float:
    """
    Returns brightness 0.0 → 1.0 based on *Stockholm local time*,
    simulating Greek summer day lighting:
    Sunrise 06:00, Sunset 20:00, Peak at 13:00.
    stockholm_offset is from API response.
    """
    # Get Stockholm local time
    t = unix_time + stockholm_offset
    hour = (t % 86400) / 3600  # local hour 0.0 → 23.999

    # Before sunrise or after sunset → lights off
    if hour < 6 or hour > 20:
        return 0.0

    # Smooth brightness curve using sine wave
    # Map 6:00 → 0, 20:00 → π → peak at 13:00
    angle = (hour - 6) * math.pi / 14
    return math.sin(angle)

# Setup watchdog timer for resetting the board if problems occur
def start_watchdog():
    microcontroller.watchdog.timeout = 8.3
    microcontroller.watchdog.mode = WatchDogMode.RESET

WATCHDOG_ENABLED = False
if WATCHDOG_ENABLED:
    start_watchdog()

# WIFI credentials
SSID = "SSID"
WPAKEY = "PASSWORD"

# URLs and tokens
TIME_SERVER_URL = "http://worldclockapi.com/api/json/cet/now"

## Time
server_time = 0
last_fetched_server_time = 0
stockholm_offset_str = "+01:00:00"  # fallback in case API fails

# Connect to wifi and start session
def wifi_connect(ssid, wpakey) -> adafruit_requests.Session:
    wifi.radio.connect(ssid, wpakey)
    print("Connected to wifi!")
    pool = socketpool.SocketPool(wifi.radio)
    session = adafruit_requests.Session(pool, ssl.create_default_context())
    print("Session started!")
    return session

def update_time_from_server() -> None:
    global http_session, server_time, stockholm_offset, last_fetched_server_time
    response = http_session.get(TIME_SERVER_URL).json()

    # Windows FILETIME to UNIX time conversion
    currentFileTime = int(response["currentFileTime"])
    server_time = int(currentFileTime / 10_000_000 - 11644473600)

    # Store Stockholm offset for later use
    stockholm_offset_str = response.get("utcOffset", "+01:00:00")
    stockholm_offset = parse_utc_offset(stockholm_offset_str)

    last_fetched_server_time = time.monotonic()

def unix_time_now() -> int:
    global server_time, last_fetched_server_time
    return int(server_time + int(time.monotonic() - last_fetched_server_time))

def feed_watchdog(mark: str = None) -> None:
    if WATCHDOG_ENABLED:
        watchdog.feed()
    global watchdog_location
    if mark:
        watchdog_location = mark
        print(f"<>{mark}")

### MAIN
# Connect to wifi
feed_watchdog("wifi")
http_session = wifi_connect(SSID, WPAKEY)

# Fetch time from server
feed_watchdog("server_time")
update_time_from_server()
unix_time_now()

small_timer = 0
while True:
    # Adjust light based on Stockholm time, Greek summer profile
    feed_watchdog("adjusting light")
    now_unix = unix_time_now()
    brightness = greek_summer_light(now_unix, stockholm_offset)
    print("Brightness:", brightness)
    set_led_brightness(brightness)

    # Sleep
    feed_watchdog("idling")
    time.sleep(3)
