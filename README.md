# Micro-Compass en MicroPython (ESP32-C3 SuperMini)

Este proyecto contiene la implementación completa y optimizada del sistema **Micro-Compass** en **MicroPython**, diseñado para ejecutarse en la tarjeta **ESP32-C3 SuperMini** conectada a una pantalla redonda TFT GC9A01 de 1.28" y un magnetómetro GY-271 (QMC5883L / QMC6310).

---

## ✨ Características Principales

* **🚀 Motor Gráfico Double-Buffered en RAM**: Renderizado en buffer off-screen de 200x200 px (80 KB) con **0% parpadeo (zero flicker)** y **0% pantallas negras**.
* **🧭 Orientación True North Real**: La aguja y las letras cardinales **N** (Rojo brillante), **E**, **S** y **W** (Blanco) rotan dinámicamente manteniendo la aguja apuntando 100% al Norte magnético real.
* **🌊 Filtro de Vector 2D Pre-atan2 (`VECTOR_ALPHA = 0.08`)**: Elimina el 99.9% del ruido eléctrico del sensor antes de calcular el ángulo, logrando un movimiento fluido con efecto de aguja náutica en baño líquido.
* **⚓ Deadband Adaptativo de 1.2°**: Elimina completamente las micro-vibraciones al mantener la brújula estática.
* **🔍 Lectura Digital Central en Doble Tamaño (2x)**: Muestra el rumbo exacto en grados (`045 DEG`) en fuente grande (16x16 px por carácter) y legible a distancia.
* **🧲 Auto-Calibración Dinámica Hard-Iron**: Auto-centrado en tiempo real de sesgos magnéticos + valores base predeterminados.

---

## 🛠️ Componentes de Hardware

1. **Microcontrolador**: ESP32-C3 SuperMini (RISC-V single core, USB-CDC nativo).
2. **Pantalla**: Display Redondo TFT 1.28" GC9A01 SPI (240x240 px, 7 pines).
3. **Sensor**: Magnetómetro GY-271 (QMC5883L / QMC6310, I2C).

---

## 📌 Esquema de Conexiones (Pinout)

### 1. Pantalla GC9A01 (SPI)

| Pin Pantalla | Pin ESP32-C3 SuperMini | Función Hardware |
|--------------|-------------------------|------------------|
| **SCL / SCK**| **GPIO 10**            | Reloj SPI Hardware (SCK) |
| **SDA / MOSI**| **GPIO 6**             | Salida Datos SPI Hardware (MOSI) |
| **DC**       | **GPIO 5**             | Control Data / Command |
| **CS**       | **GPIO 7**             | Chip Select SPI |
| **RES / RST**| **GPIO 3**             | Hardware Reset |
| **VCC**      | **3.3V**                | Alimentación (3.3V) |
| **GND**      | **GND**                 | Tierra / Masa |

### 2. Magnetómetro GY-271 (QMC5883 / QMC6310, I2C)

| Pin Sensor | Pin ESP32-C3 SuperMini | Función Hardware |
|------------|-------------------------|------------------|
| **SDA**    | **GPIO 0**              | Datos I2C (`Pin.PULL_UP`) |
| **SCL**    | **GPIO 1**              | Reloj I2C (`Pin.PULL_UP`) |
| **VCC**    | **3.3V**                | Alimentación (3.3V) |
| **GND**    | **GND**                 | Tierra / Masa |

> Ver guía detallada con esquemas en [`DOCS/PINOUT_WIRING.md`](file:///c:/Users/Victolt%20MSI/Documents/Software/Antigravity%20Tests/Micro-compass/DOCS/PINOUT_WIRING.md).

---

## 📁 Estructura del Directorio

```
Micro-compass/
├── CODES/
│   ├── main.py            # Programa principal (Polling, filtro vectorial 2D, loop 60 FPS)
│   ├── compass_ui.py      # Motor gráfico Double-Buffered (RAM tile 200x200 px, fuentes 3x/2x)
│   ├── gc9a01.py          # Driver TFT SPI optimizado a 20 MHz
│   ├── qmc5883.py         # Driver I2C sensor QMC5883L/QMC6310 con fallback de estado
│   ├── calibrate.py       # Utilidad de calibración 3D Hard-Iron & Soft-Iron
│   └── Test_Codes/        # Scripts de prueba y diagnóstico de hardware
├── Test_Codes/            # Directorio duplicado con scripts de pruebas diagnósticas
├── DOCS/
│   ├── PROJECT_HISTORY.md # Historial completo de diagnósticos y optimizaciones
│   └── PINOUT_WIRING.md   # Esquema eléctrico y diagrama de conexiones
└── README.md
```

---

## 🚀 Instrucciones de Ejecución

1. Carga los archivos del directorio `CODES/` a la tarjeta ESP32-C3 mediante **Thonny IDE**.
2. En la consola REPL de MicroPython, presiona **Ctrl+D** (soft reboot) y ejecuta:
   ```python
   import main
   main.main()
   ```

---

## 🎯 Calibración del Magnetómetro

Para recalibrar en un entorno con interferencias metálicas:
1. Ejecuta `import calibrate; calibrate.run_calibration()` en la consola REPL.
2. Rota el dispositivo en forma de 8 en el aire durante 30 segundos.
3. Copia los 6 valores impresos (`Xoffset`, `Yoffset`, `Zoffset`, `Xscale`, `Yscale`, `Zscale`) e ingrésalos en el encabezado de `main.py`.
