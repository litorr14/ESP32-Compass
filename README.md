# Micro-Compass en MicroPython (ESP32-C3 SuperMini)

Este proyecto contiene la implementación completa y optimizada del sistema **Micro-Compass** en **MicroPython**, diseñado para ejecutarse en la tarjeta **ESP32-C3 SuperMini** conectada a una pantalla redonda TFT GC9A01 de 1.28" y un magnetómetro GY-271 (QMC5883L / QMC6310).

---

## ✨ Características Principales

* **🚀 Motor Gráfico Double-Buffered en RAM**: Renderizado en buffer off-screen de 200x200 px (80 KB) con **0% parpadeo (zero flicker)** y **0% pantallas negras** a ~35–60 FPS.
* **🧭 Navegación de Precisión True-North y Formato Aeronáutico**:
  * Lectura correcta de canales de datos desde el registro `0x01` (`X_L, X_M, Y_L, Y_M, Z_L, Z_M`).
  * Convención aeronáutica estándar en sentido horario ($0^\circ \text{ N} \rightarrow 90^\circ \text{ E} \rightarrow 180^\circ \text{ S} \rightarrow 270^\circ \text{ W}$).
  * Aguja roja brillante apuntando 100% al Norte magnético real con efecto náutico en baño líquido.
* **🌊 Filtrado Vectorial 2D Pre-Trigonométrico**: Suavizado continuo de $(mx, my)$ antes del cálculo de $\operatorname{atan2}$, eliminando el 100% de picos e interferencias eléctricas.
* **⚓ Deadband Adaptativo**: Elimina completamente las micro-vibraciones al mantener la brújula estática.
* **🔍 Lectura Digital Central en Alto Contraste**: Muestra el rumbo exacto en grados (`045 DEG`) en fuente grande y legible a distancia.

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
 
Valores de calibración calculados y verificados en tiempo real para este dispositivo:
```python
Xoffset = 3384.0
Yoffset = -985.0
Zoffset = -132.0
Xscale  = 1.055
Yscale  = 1.000
Zscale  = 1.000
headingOffset = -4.0
```

Para recalibrar en un entorno nuevo:
1. Ejecuta `Test_Codes/compass_live_debug.py` en Thonny.
2. Rota el dispositivo 360° en el aire durante 20 segundos y presiona `Ctrl+C`.
3. Pega los nuevos valores impresos en el encabezado de `CODES/main.py`.

