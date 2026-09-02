# Micro-Compass Hardware Pinout & Inter-Module Wiring Guide

**System**: Micro-Compass  
**Microcontroller**: ESP32-C3 SuperMini (RISC-V Architecture)  
**Display**: GC9A01 1.28" 240x240 Round TFT Display (7-Pin SPI)  
**Sensor**: GY-271 3-Axis Magnetometer (QMC5883L / QMC6310, I2C)  

---

## 📌 1. Master System Wiring Matrix

```
                      +-------------------------+
                      |   ESP32-C3 SuperMini    |
                      +-------------------------+
                       | 3.3V  GND  IO0  IO1 |
                       |   |    |    |    |  |
        +--------------+   |    |    |    +--|------------------+
        |                  |    |    |       |                  |
        v                  v    v    v       v                  v
+---------------+        +---------------+        +-------------------+
|  GC9A01 TFT   |        |  Power Rails  |        | GY-271 Sensor     |
| (240x240 SPI) |        | (3.3V & GND)  |        | (QMC5883 / 6310)  |
+---------------+        +---------------+        +-------------------+
| VCC   -> 3.3V |        | 3.3V -> VCC   |        | VCC  -> 3.3V      |
| GND   -> GND  |        | GND  -> GND   |        | GND  -> GND       |
| SCL   -> GPIO10 (SPI SCK)              | SDA  -> GPIO0 (SoftI2C) |
| SDA   -> GPIO6  (SPI MOSI)             | SCL  -> GPIO1 (SoftI2C) |
| DC    -> GPIO5  (Data/Command)         +-------------------+
| CS    -> GPIO7  (Chip Select)
| RES   -> GPIO3  (Reset)
+---------------+
```

---

## 🖥️ 2. GC9A01 Round TFT Display Connections (SPI)

| Display Pin | Label on Display | ESP32-C3 SuperMini Pin | Hardware Function | Notes |
|-------------|------------------|-------------------------|-------------------|-------|
| 1 | **VCC** | **3.3V** | Power (3.3V) | Connect to 3.3V power rail |
| 2 | **GND** | **GND** | Ground | Connect to common GND rail |
| 3 | **SCL / SCK** | **GPIO 10** | SPI Clock (SCK) | Hardware SPI1 Bus |
| 4 | **SDA / MOSI** | **GPIO 6** | SPI Data (MOSI) | Hardware SPI1 Bus |
| 5 | **DC** | **GPIO 5** | Data / Command Control | GPIO Output |
| 6 | **CS** | **GPIO 7** | SPI Chip Select | GPIO Output |
| 7 | **RES / RST** | **GPIO 3** | Hardware Reset | GPIO Output |

> [!NOTE]  
> Strapping pins **GPIO 2, GPIO 8, and GPIO 9** on the ESP32-C3 SuperMini were deliberately avoided to prevent boot mode lockups during power-on reset.

---

## 🧲 3. GY-271 Magnetometer Connections (I2C)

| Sensor Pin | Label on Sensor | ESP32-C3 SuperMini Pin | Hardware Function | Notes |
|------------|-----------------|-------------------------|-------------------|-------|
| 1 | **VCC** | **3.3V** | Power (3.3V) | Connect to 3.3V power rail |
| 2 | **GND** | **GND** | Ground | Connect to common GND rail |
| 3 | **SDA** | **GPIO 0** | I2C Data (SDA) | Internal Pull-Up Enabled (`Pin.PULL_UP`) |
| 4 | **SCL** | **GPIO 1** | I2C Clock (SCL) | Internal Pull-Up Enabled (`Pin.PULL_UP`) |

> [!TIP]  
> MicroPython initializes I2C using `SoftI2C(sda=Pin(0, Pin.IN, Pin.PULL_UP), scl=Pin(1, Pin.IN, Pin.PULL_UP), freq=100000)`. If using long jumper wires (> 10 cm), add external **4.7kΩ pull-up resistors** from SDA to 3.3V and SCL to 3.3V.

---

## ⚡ 4. Power Distribution & Electrical Specifications

- **Operating Voltage**: 3.3V DC (Do NOT connect 5V directly to GC9A01 or GY-271 signal lines!).
- **Peak Current Consumption**:
  - ESP32-C3 SuperMini (Active Wi-Fi/BT off): ~40–60 mA
  - GC9A01 1.28" TFT Backlight: ~30–45 mA
  - GY-271 Magnetometer (Continuous sampling): ~1–2 mA
  - **Total System Current**: ~75–100 mA (Easily powered via USB-C or 3.7V LiPo battery through onboard 3.3V LDO regulator).

---

## 🛠️ 5. Software Pin Configuration Mapping (`main.py`)

```python
# Hardware SPI Configuration (GC9A01 Display)
PIN_SCK  = 10  # GPIO 10 (SCL on display)
PIN_MOSI = 6   # GPIO 6  (SDA on display)
PIN_DC   = 5   # GPIO 5  (DC on display)
PIN_CS   = 7   # GPIO 7  (CS on display)
PIN_RST  = 3   # GPIO 3  (RES on display)

# Software I2C Configuration (GY-271 Magnetometer Sensor)
PIN_SDA  = 0   # GPIO 0
PIN_SCL  = 1   # GPIO 1
```
