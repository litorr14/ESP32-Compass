"""
Micro-Compass Main Application for ESP32-C3 SuperMini in MicroPython.
Uses QMC5883 / HMC5883 (GY-271) Magnetometer and GC9A01 240x240 Round TFT Display.
"""

import math
import time
import sys
from machine import Pin, SPI, I2C

from gc9a01 import GC9A01
from qmc5883 import QMC5883
from compass_ui import CompassUI

# Pin Configuration (ESP32-C3 SuperMini HW-466AB)
# SPI - Display GC9A01
PIN_SCK  = 10  # GPIO 10 (SCL on display)
PIN_MOSI = 6   # GPIO 6  (SDA on display)
PIN_DC   = 5   # GPIO 5  (DC on display)
PIN_CS   = 7   # GPIO 7  (CS on display)
PIN_RST  = 3   # GPIO 3  (RES on display)

# I2C - Sensor GY-271 (QMC5883 / HMC5883)
PIN_SDA  = 0   # GPIO 0
PIN_SCL  = 1   # GPIO 1

# Default Calibration Parameters (Run calibrate.py to customize for your environment)
Xoffset = -640.0
Yoffset = 779.0
Zoffset = 509.0

Xscale = 1.0
Yscale = 1.0
Zscale = 1.0

# Sensor mounting orientation offset (in degrees)
headingOffset = 0.0

# Exponential Smoothing Low-Pass Filter Alpha (0.22 = smooth liquid-damped compass feel)
FILTER_ALPHA = 0.22

def angle_difference(from_angle, to_angle):
    """Calculate shortest angular difference between two angles in degrees (-180 to +180)."""
    diff = to_angle - from_angle
    while diff > 180.0:
        diff -= 360.0
    while diff < -180.0:
        diff += 360.0
    return diff

def main():
    print("Initializing Micro-Compass on ESP32-C3 SuperMini...")
    time.sleep_ms(300)

    # Initialize high-speed SPI for GC9A01 Display (20MHz Hardware SPI)
    try:
        spi = SPI(1, baudrate=20000000, sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI))
    except Exception:
        try:
            from machine import SoftSPI
            spi = SoftSPI(sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(8), baudrate=20000000)
        except Exception:
            spi = SPI(0, baudrate=20000000, sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI))

    dc = Pin(PIN_DC, Pin.OUT)
    cs = Pin(PIN_CS, Pin.OUT)
    rst = Pin(PIN_RST, Pin.OUT)

    display = GC9A01(spi, dc=dc, cs=cs, rst=rst, rotation=0)
    ui = CompassUI(display)

    # Initialize SoftI2C for Magnetometer Sensor (SDA=GPIO0, SCL=GPIO1)
    from machine import SoftI2C
    try:
        i2c = SoftI2C(sda=Pin(PIN_SDA, Pin.IN, Pin.PULL_UP), scl=Pin(PIN_SCL, Pin.IN, Pin.PULL_UP), freq=100000)
    except Exception:
        i2c = I2C(0, sda=Pin(PIN_SDA, Pin.IN, Pin.PULL_UP), scl=Pin(PIN_SCL, Pin.IN, Pin.PULL_UP), freq=100000)

    try:
        qmc = QMC5883(i2c)
        print(f"Magnetometer found and initialized at address 0x{qmc.address:02X}!")
    except Exception as err:
        print("Magnetometer not found!", err)
        ui.draw_error_screen(
            "Sensor Error...",
            [
                "Sensor initialization failed",
                "or",
                "Sensor wiring incorrect",
                "or",
                "Faulty sensor"
            ]
        )
        while True:
            time.sleep(1)

    # Dynamic Hard-Iron Auto-Centering bounds
    min_x, max_x = 32767, -32768
    min_y, max_y = 32767, -32768

    # Low-Pass Filtered Magnetic Vector components (Pre-atan2 filtering eliminates 99.9% sensor noise!)
    smooth_x = None
    smooth_y = None
    VECTOR_ALPHA = 0.08  # Heavy liquid-damped nautical compass feel

    # State variables
    first_reading = True
    last_rendered_heading = 0.0

    # Initial screen draw
    ui.draw_static_dial()

    print("Compass active. Polling sensor...")

    last_poll = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_poll) >= 10:  # 10ms interval (~60-100 FPS)
            last_poll = now

            raw_data = qmc.read_raw()
            if raw_data is not None:
                x_raw, y_raw, z_raw = raw_data

                # 1. Low-Pass Filter RAW 2D vectors BEFORE atan2 (eliminates electronic sensor noise!)
                if smooth_x is None:
                    smooth_x = float(x_raw)
                    smooth_y = float(y_raw)
                else:
                    smooth_x += VECTOR_ALPHA * (x_raw - smooth_x)
                    smooth_y += VECTOR_ALPHA * (y_raw - smooth_y)

                # 2. Track min/max to auto-center Hard-Iron offset dynamically
                if smooth_x < min_x: min_x = smooth_x
                if smooth_x > max_x: max_x = smooth_x
                if smooth_y < min_y: min_y = smooth_y
                if smooth_y > max_y: max_y = smooth_y

                # Calculate effective Hard-Iron offsets
                if Xoffset != 0.0:
                    curr_x_off = Xoffset
                elif max_x > min_x:
                    curr_x_off = (max_x + min_x) / 2.0
                else:
                    curr_x_off = 0.0

                if Yoffset != 0.0:
                    curr_y_off = Yoffset
                elif max_y > min_y:
                    curr_y_off = (max_y + min_y) / 2.0
                else:
                    curr_y_off = 0.0

                # 3. Apply calibration scaling and offset
                x = (smooth_x - curr_x_off) * Xscale
                y = (smooth_y - curr_y_off) * Yscale
                y = -y

                # 4. Calculate clean magnetic heading in degrees
                heading = (math.degrees(math.atan2(y, x)) + headingOffset) % 360.0
                if heading < 0:
                    heading += 360.0

                # 5. Refresh display UI when heading changes by at least 1.2 deg to eliminate all vibration
                if first_reading:
                    last_rendered_heading = heading
                    first_reading = False
                    ui.update(heading)
                else:
                    if abs(angle_difference(last_rendered_heading, heading)) >= 1.2:
                        last_rendered_heading = heading
                        ui.update(heading)

        time.sleep_ms(2)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys
        print("\n" + "="*40)
        print("❌ UNCAUGHT EXCEPTION IN MAIN:")
        print("="*40)
        sys.print_exception(e)
        print("="*40 + "\n")
        while True:
            time.sleep(1)
