# Micropython RP2040 Joystick Library

This is a lightweight and efficient joystick library for Micropython on RP2040-based boards.
It supports analog joystick input with calibration, button reading, and asynchronous input detection.
This library was developed for the RP2040 but may work on other Micropython boards if you adapt the pin assignments.

## Features

- Automatic joystick calibration with easy interactive setup (just calibrate in the position your joystick is mounted, even if it's rotated. The library will handle it.)
- Analog input reading with smoothing (averaging samples)
- Direction detection with percentage-based sensitivity
- Button press detection
- Asynchronous waiting for input events (using `asyncio`)
- Optimized for performance with `@micropython.native` decorators

## Installation

Simply copy `joystick.py` into your project folder or `lib` directory on your RP2040 Micropython device.

## Usage

Please run this file the first time directly to calibrate the joystick (calibrations will be saved into the same file).

### 🔧 Constructor Parameters

You can adjust the behavior of the joystick by passing optional parameters when creating the object:

```python
Joystick(a1, a2, button_pin, samples=3, deadzone=10, async_timeout=10)
```

| Parameter       | Type   | Default | Description                                                                 |
|----------------|--------|---------|-----------------------------------------------------------------------------|
| `a1`, `a2`      | `int`  | —       | ADC IDs for the two axis.                                        |
| `button_pin`    | `int`  | —       | GPIO pin number for the joystick button.                                   |
| `samples`       | `int`  | `3`     | Number of ADC samples to average per axis read. Higher = smoother but slower. |
| `deadzone`      | `int`  | `3`    | Percentage range around the center that counts as "neutral" (prevents small input noise). |
| `async_timeout` | `int`  | `10`    | Delay in milliseconds between checks in `get_waiter()` or `button_waiter()` (used with asyncio). |


Examples:

```python
from joystick import Joystick
import asyncio

# Initialize joystick with ADC IDs and button pin
joystick = Joystick(a1=0, a2=1, button_pin=22)  # Adjust pins accordingly

async def main():
    while True:
        input_event = await joystick.get_waiter()
        print("Joystick event:", input_event)

asyncio.run(main())


# Also works without asyncio:

from joystick import Joystick
import time

# Initialize joystick with ADC IDs and button pin
joystick = Joystick(a1=0, a2=1, button_pin=22)  # Adjust pins accordingly

while True:
    event = joystick.get()
    if event:
        print("Joystick event:", event)
    time.sleep(0.01)  # Polling delay
