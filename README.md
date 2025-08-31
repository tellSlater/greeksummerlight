# Greek Summer Light 🌞

A **Raspberry Pi Pico W** project that simulates **Greek summer daylight** using an LED strip.  
The LED brightness smoothly follows a sine wave, peaking at **13:00**, fading in at **06:00 (sunrise)**,  
and fading out at **20:00 (sunset)** — based on **local time**, automatically adjusted for DST.

---

## ✨ Features
- 🌍 **Automatic Time Sync**  
  Uses the [WorldClock API](http://worldclockapi.com) to fetch accurate **local time**.
- 🕒 **DST-Aware**  
  Automatically adjusts between **UTC+1** and **UTC+2**.
- ☀️ **Greek Summer Profile**  
  - Sunrise → **06:00**  
  - Sunset → **20:00**  
  - Peak brightness → **13:00**
- 💡 **Smooth LED Brightness**  
  Uses a sine curve for natural brightness transitions.
- 🔄 **Watchdog Support** *(optional)*  
  Resets the Pico if it freezes.
- 📶 **Wi-Fi Connectivity**  
  Auto-connects and keeps session alive.

---

## 🛠 Hardware Requirements
- **Raspberry Pi Pico W**
- LED strip (PWM controlled)
- Resistor & transistor (if required for current handling)
- Wi-Fi connection

---

## 📦 Software & Libraries
- **CircuitPython** (Adafruit)
- [`adafruit_requests`](https://docs.circuitpython.org/projects/requests/en/latest/)
- `wifi`, `ssl`, `socketpool`
- `pwmio`, `math`, `board`

---

## ⚙️ Setup
1. Flash **CircuitPython** on your Pico W.
2. Install the required libraries into `lib/` on your Pico.
3. Edit the Wi-Fi credentials in `main.py`:
   ```python
   SSID = "your_wifi"
   WPAKEY = "your_password"
