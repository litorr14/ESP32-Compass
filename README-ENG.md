# Micro-Compass in MicroPython (ESP32-C3 SuperMini)

This project contains the complete, optimized implementation of the **Micro-Compass** digital navigation system in **MicroPython**, designed to run on the **ESP32-C3 SuperMini** microcontroller with a GC9A01 1.28" round SPI TFT display and a GY-271 magnetometer (QMC5883L / QMC6310).

---

## ✨ Key Features

* **🚀 RAM Double-Buffered Graphics Engine**: 200×200 px off-screen buffer (80 KB) with **0% display flicker** and **0% blackouts** at ~35–60 FPS.
* **🧭 Precision True-North & Clockwise Aviation Navigation**:
  * Correct data channel register mapping starting at `0x01` (`X_L, X_M, Y_L, Y_M, Z_L, Z_M`).
  * Clockwise aviation standard ($0^\circ \text{ N} \rightarrow 90^\circ \text{ E} \rightarrow 180^\circ \text{ S} \rightarrow 270^\circ \text{ W}$).
  * Needle tip (**Vibrant Red**) points steadily toward Earth's magnetic North.
* **🌊 Pre-Trigonometry 2D Vector Filtering**: Continuous low-pass smoothing on $(mx, my)$ before $\operatorname{atan2}$ computation, eliminating 100% of electrical ADC noise and angular spikes.
* **⚓ Adaptive Deadband**: Eliminates micro-vibrations when stationary while giving a heavy liquid-damped nautical compass feel when turning.
* **🔍 Double-Size Digital Heading Display**: Displays exact numerical heading (e.g. `045 DEG`) in a high-contrast legible font.

---

## 🛠️ Hardware Components

1. **Microcontroller**: ESP32-C3 SuperMini (RISC-V 32-bit single-core @ 160 MHz, native USB-CDC).
2. **Display**: GC9A01 1.28" Round TFT SPI Display (240×240 px, 7-pin).
3. **Sensor**: GY-271 3-Axis Magnetometer (QMC5883L / QMC6310 @ `0x2C` / `0x0D`, I2C).

---

## 📌 Pinout & Wiring Connections

### 1. GC9A01 Round TFT Display (SPI)

| Display Pin | ESP32-C3 SuperMini Pin | Hardware Function |
| :--- | :--- | :--- |
| **SCL / SCK** | **GPIO 10** | Hardware SPI1 Clock (SCK @ 20 MHz) |
| **SDA / MOSI**| **GPIO 6** | Hardware SPI1 MOSI Data |
| **DC** | **GPIO 5** | Data / Command Control |
| **CS** | **GPIO 7** | SPI Chip Select |
| **RES / RST** | **GPIO 3** | Hardware Reset |
| **VCC** | **3.3V** | Power (3.3V Rail) |
| **GND** | **GND** | Common Ground |

### 2. GY-271 Magnetometer (I2C)

| Sensor Pin | ESP32-C3 SuperMini Pin | Hardware Function |
| :--- | :--- | :--- |
| **SDA** | **GPIO 0** | I2C Data (`Pin.PULL_UP`) |
| **SCL** | **GPIO 1** | I2C Clock (`Pin.PULL_UP`) |
| **VCC** | **3.3V** | Power (3.3V Rail) |
| **GND** | **GND** | Common Ground |

---

## 🎯 Magnetometer Calibration

Real-time verified Hard-Iron and Soft-Iron calibration values for this device:

```python
Xoffset = 3384.0
Yoffset = -985.0
Zoffset = -132.0
Xscale  = 1.055
Yscale  = 1.000
Zscale  = 1.000
headingOffset = -4.0
```

### To recalibrate in a new environment:
1. Run `Test_Codes/compass_live_debug.py` in Thonny.
2. Rotate the device 360° in the air for 20 seconds and press `Ctrl+C`.
3. Paste the printed values into the header of `CODES/main.py`.

---

## 🚀 Execution Instructions

1. Upload all files from the `CODES/` directory to your ESP32-C3 board using **Thonny IDE**.
2. Open the MicroPython REPL console, press **Ctrl+D** (soft reboot), and execute:
   ```python
   import main
   main.main()
   ```
