# MicroPython Code Documentation - `_blinx_output_sensor.py`

This file contains code for controlling output sensors in the Blinx system using MicroPython.

## Dependencies
The code has the following dependencies:
- `_blinx_blinx` module as `blinx`
- `machine` module from MicroPython
  - `ADC`, `PWM`, and `Pin` classes from the `machine` module
- `uasyncio` module from MicroPython
- `time` module from MicroPython

## Functions

### `output_screen(args)`
This function is used to write text on the screen.
#### Arguments
- `args` (list): List of text strings to be displayed on the screen.

### `output_led_buzzer(args)`
This function is used to control the LED and buzzer connected to pin 8.
#### Arguments
- `args` (list): List of optional arguments for controlling the LED and buzzer. The arguments can be:
  - If `len(args) == 0`, the LED or buzzer is turned off.
  - If `len(args) == 1`, the `args[0]` value determines the behavior. It can be:
    - `'on'`: Turn the LED or buzzer on.
    - `'off'`: Turn the LED or buzzer off.
    - An integer value: Set the PWM duty cycle for the LED or buzzer.
  - If `len(args) == 2`, the `args[0]` value determines the PWM duty cycle, and `args[1]` determines the frequency.
  - If `len(args) == 3`, the `args[0]` value determines the PWM duty cycle, `args[1]` determines the frequency, and `args[2]` determines the timeout in seconds.

### `get_output_port(n, m)`
This function returns a lambda function to control the output port specified by `n` and `m`, it can be : `p1a`, `p1b`, `p2a`, `p2b`.
#### Arguments
- `n` (int): The port number (1 or 2).
- `m` (int): The sub-port number (1 or 2).
#### Return
Lambda function

### `output_port_general(n, m, args)`
This function is used to control the output ports (excluding pin 8).
#### Arguments
- `n` (int): The port number (1 or 2).
- `m` (int): The sub-port number (1 or 2).
- `args` (list): List of optional arguments for controlling the output port. The arguments follow the same format as `output_led_buzzer(args)`.

### `remove_pwm(port, pwm = 0, freq = 5000)`
This function removes the PWM output from the specified port.
#### Arguments
- `port`: The port from which to remove the PWM output.
- `pwm` (int): The duty cycle for the PWM output (default: 0).
- `freq` (int): The frequency of the PWM output (default: 5000).

### `remove_dig(port, value = 0)`
This function removes the digital output from the specified port.
#### Arguments
- `port`: The port from which to remove the digital output.
- `value` (int): The value to set on the port (default: 0).

### `save_output_sensors(port)`
This function returns the saved output value for the specified port.
#### Arguments
- `port` (int): The port for which to retrieve the saved output value.
#### Return
The saved output value for the specified port.

### `save_output_sensors_csv(value, times_sensors)`
This function formats the output value for saving it in a CSV file.
#### Arguments
- `value` (int): The output value to format.
- `times_sensors` (int): The number of times the output value has been read.
#### Return
The formatted output value as a string

### `remove_output_value()`
This function removes the output value after a timeout.

## Variables

### `screen_modify`
A global boolean variable that indicates whether the screen has been modified.

### `value_output`
A global list that stores the output values for each port.

### `can_be_removed`
A global list that stores the timeout and removal functions for each port.

### `dict_sensors_output`
A dictionary mapping sensor names to their corresponding output functions.

### `modify_port_input`
A global variable used to modify port inputs.

## Example usage:
```python# Example usage of the output screen function
output_screen(["Hello, World!"])

# Example usage of the output LED/buzzer function
output_led_buzzer([512])  # Sets the LED/buzzer intensity to 512
output_led_buzzer([512, 1000])  # Sets the LED/buzzer intensity to 512 and frequency to 1000
output_led_buzzer([512, 1000, 5])  # Sets the LED/buzzer intensity to 512, frequency to 1000, and timeout to 5

# Example usage of the output port general function
output_port_general(1, 1, [])  # Sets the output port p1a intensity to 0, it is equal to turns off the output port p1a
output_port_general(2, 2, [512])  # Sets the output port p2b intensity to 512
output_port_general(1, 2, [512, 1000])  # Sets the output port p1b intensity to 512 and frequency to 1000
output_port_general(2, 1, [512, 1000, 5])  # Sets the output port p2a intensity to 512, frequency to 1000, and timeout to 5

# Example usage of the remove_pwm function
remove_pwm(pin)  # Removes PWM output on the specified pin

# Example usage of the remove_dig function
remove_dig(pin)  # Removes digital output on the specified pin

# Example usage of the get_save_output_sensors function
get_sensor_value = get_save_output_sensors(0)  # Get a lambda function to retrieve the value of output sensor 0
sensor_value = get_sensor_value()  # Retrieve the value of output sensor 0

# Example usage of the save_output_sensors function
sensor_value = save_output_sensors(0)  # Save the value of output sensor 0

# Example usage of the save_output_sensors_csv function
csv_value = save_output_sensors_csv(512, 1)  # Convert output sensor value to CSV format

# Example usage of the remove_output_value function
remove_output_value()  # Remove the output value after the specified timeout

```