# Summer Light — Pico W (CircuitPython)

Simulate **summer daylight** on an LED using **Stockholm local time** for the clock.  
Time syncs via **Adafruit NTP once per day**, then runs on **`time.monotonic()`** (no drift from sleeps). No HTTP/JSON.

## Features
- **Daily NTP sync** with `adafruit_ntp`; **offline** monotonic timing between syncs.
- **No external time APIs** (no `adafruit_requests`, no worldtime services).
- **Stockholm DST** handled locally (EU rule: last Sun in Mar 01:00 UTC → last Sun in Oct 01:00 UTC).
- **Summer profile**: smooth sine brightness from **06:00 → 20:30**, peak at midday; optional gamma.
- **Resilient**: keeps running if NTP fails; retries later.

## Hardware
- **Raspberry Pi Pico W**
- LED driven from a PWM pin (default: `GP15`) with suitable transistor/resistor as needed.

## Software / Libraries
- **CircuitPython** (tested on 9.x)
- Built-ins: `wifi`, `socketpool`, `time`, `math`, `pwmio`, `board`
- One external lib in `/lib/`: **`adafruit_ntp.mpy`**
  - _Not used anymore_: `adafruit_datetime`, `adafruit_requests`.

## Files & Layout

