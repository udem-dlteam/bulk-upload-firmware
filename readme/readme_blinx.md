# MicroPython Code Documentation - `_blinx_blinx.py`

This file contains pin assignments and initialization code for various components used in the project.

## Variables

### `scl_pin_num` (integer)
The pin number assigned to the I2C SCL (clock) pin.

### `sda_pin_num` (integer)
The pin number assigned to the I2C SDA (data) pin.

### `port_pin_nums` (list)
A list of pin numbers assigned to each port. Each port has two signals.

### `button_pin_nums` (list)
A list of pin numbers assigned to the left and right buttons.

### `led_pin_num` (integer)
The pin number assigned to the LED and buzzer (shared pin).

### `buzzer_pin_num` (integer)
The pin number assigned to the buzzer.

### `periph_power_pin_num` (integer)
The pin number assigned to the peripheral power.

## Functions

### `input_pin(i)`
This function creates an input Pin object with pull-up enabled for the specified pin number.

#### Arguments
- `i` (integer): The pin number to create an input Pin object for.

#### Return
- A Pin object configured as an input pin with pull-up enabled.

### `output_pin(i)`
This function creates an output Pin object with pull-up enabled for the specified pin number.

#### Arguments
- `i` (integer): The pin number to create an output Pin object for.

#### Return
- A Pin object configured as an output pin with pull-up enabled.

### `button(i)`
This function checks the value of the specified button.

#### Arguments
- `i` (integer): The index of the button to check.

#### Return
- `True` if the button is pressed (value is 0), `False` otherwise.

### `led(on)`
This function controls the LED.

#### Arguments
- `on` (boolean): Specifies whether to turn the LED on (`True`) or off (`False`).

### `periph_power(on)`
This function controls the peripheral power.

#### Arguments
- `on` (boolean): Specifies whether to turn on (`True`) or off (`False`) the peripheral power.

### `i2c_init()`
This function initializes the I2C interface using the specified SCL and SDA pins.

## Usage Example

```python
import _blinx_blinx

# Example usage of `button()`
left_button_pressed = _blinx_blinx.button(_blinx_blinx.LEFT)
if left_button_pressed:
    print("Left button is pressed.")

# Example usage of `led()`
_led_on = True  # Replace with the desired LED state
_blinx_blinx.led(_led_on)

# Example usage of `periph_power()`
_periph_power_on = True  # Replace with the desired peripheral power state
_blinx_blinx.periph_power(_periph_power_on)

# Example usage of `i2c_init()`
_blinx_blinx.i2c_init()
```
