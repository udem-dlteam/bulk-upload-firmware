# MicroPython Code Documentation - `_blinx_ds1820.py`

This file contains code related to the DS1820 temperature  and humidity sensor using MicroPython for the Blinx platform.

## Dependencies
The code has the following dependencies:
- `onewire` module from MicroPython
- `ds18x20` module from MicroPython
- `machine` module from MicroPython
- `_blinx_blinx` module as `blinx`

## Functions

### `get_ds1820_function(index)`
This function returns a lambda function that reads the temperature from the DS1820 sensor at the specified index.

#### Arguments
- `index` (integer): The index of the DS1820 sensor.

#### Return
- A lambda function that reads the temperature from the DS1820 sensor.

### `byte_to_int_ds1820(n, times_sensors)`
This function converts the raw byte value to a readable temperature value.

#### Arguments
- `n` (numeric): The raw byte value representing the temperature.
- `times_sensors` (numeric): The number of times the sensors are read.

#### Return
- A formatted string representing the temperature.

### `other(*args, **kwargs)`
This function serves as a placeholder and does nothing.

### `get_sensor_analog_ds1820(n, m)`
This function tests if a DS1820 sensor is connected at the specified port and pin. If a sensor is detected, it initializes the sensor and returns the corresponding measurement function.

#### Arguments
- `n` (integer): The first index of the port.
- `m` (integer): The second index of the pin.

#### Return
- A tuple containing:
  - The measurement function for the DS1820 sensor.
  - A list of arguments required by the measurement function.
  - A boolean value indicating if the sensor is connected.

### `scan_ds1820()`
This function performs a scan to detect the presence of DS1820 sensors and updates the `ds1820_probable` list.

### `get_info()`
This function retrieves information about the DS1820 sensors and populates the `info` dictionary.

### `reset_ds1820()`
This function resets all DS1820 measurements, including resetting the onewire connections, clearing the sensor instances, and performing a new scan.

## Variables

### `ds1820_rom` (list)
A list containing the ROM IDs of the DS1820 sensors.

### `ds1820_sensor` (list)
A list containing DS18X20 sensor instances.

### `ds1820_onewire` (list)
A list containing OneWire instances for the DS1820 sensors.

### `ds1820_probable` (list)
A list indicating whether a DS1820 sensor is likely connected or not.

### `info` (dictionary)
A dictionary that stores information about the DS1820 sensors.

The structure of each entry in the `info` dictionary is as follows:
- `'function'`: The corresponding measurement function for the sensor.
- `'function_csv'`: The `byte_to_int_ds1820` function for converting the raw byte value to a readable temperature.
- `'size_csv'`: The number of digits required for the CSV representation of the temperature.
- `'type'`: The type of sensor, specified as `'in'`.
- `'char'`: A character representation of the sensor.
- `'more'`: Additional information about the sensor.
- `'use'`: A boolean value indicating if the sensor is connected.

## Usage Example

```python
import _blinx_ds1820

# Reset all DS1820 measurements
_blinx_ds1820.reset_ds1820()

# Get information about the DS1820 sensors
sensor_info = _blinx_ds1820.info

# Example usage
for sensor_name, sensor_data in sensor_info.items():
    sensor_function = sensor_data['function']
    sensor_csv_function = sensor_data['function_csv']
    size_csv = sensor_data['size_csv']
    sensor_type = sensor_data['type']
    sensor_char = sensor_data['char']
    sensor_more = sensor_data['more']
    sensor_use = sensor_data['use']
    # Perform actions using the sensor information
    ...
```