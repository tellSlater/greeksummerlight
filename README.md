# Summerlight — Pico W (CircuitPython)

**Project page:** https://wfshores.com/projects/normal/summerlight/project

**What it is (short):** A Raspberry Pi Pico W script that drives LED brightness across the day using a smooth curve,
to mimic natural daylight indoors. This isn’t just for plants—humans benefit from daylight-like cycles too
(better mood, circadian rhythm, and focus).

---

## Code description
- Single file: **`main.py`** (CircuitPython).
- **Timekeeping:** Daily NTP sync; between syncs it advances using `time.monotonic()` so there’s no sleep drift.
- **Local time:** Lightweight EU DST handling (last Sun of Mar/Oct). A `TIMEZONE` env var is read for the displayed zone name.
- **Brightness profile:** Sine-like curve from morning to evening (parameters in code). Optional gamma.
- **Output:** One PWM channel on **GP15** updates duty cycle continuously; prints periodic status lines over serial.
- **Resilience:** If Wi‑Fi/NTP isn’t available, it keeps running on the monotonic clock and retries syncing later.

### Requirements
- CircuitPython for Pico W (10.x recommended).
- `CIRCUITPY/lib/adafruit_ntp.mpy` present on the device.

### Configure
Create `settings.toml` on the CIRCUITPY drive:
```toml
CIRCUITPY_WIFI_SSID = "your-ssid"
CIRCUITPY_WIFI_PASSWORD = "your-password"
TIMEZONE = "Europe/Stockholm"   # or your preferred zone label
```
Copy **`main.py`** to the CIRCUITPY root and reset the board.

---

## Hardware (very brief)
Use any standard LED setup you like. The code expects a **logic-level MOSFET** driven from **GP15 (PWM)** to control the strip.
If you power the Pico from a 5 V buck while also programming over USB, **insert a series diode toward the Pico’s 5 V/VSYS**
to avoid **back-feeding** the rest of your hardware during flashing.

---

## License
This project is released under the **MIT License**. You’re free to use, modify, and redistribute the code (including commercially) as long as you include the copyright
notice and the license text. See the [LICENSE](LICENSE) file for details, or read the MIT terms at https://opensource.org/license/mit/.


