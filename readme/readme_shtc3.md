# MicroPython Code Documentation - `_blinx_shtc3.py`

This document provides documentation for the `_blinx_shtc3.py` MicroPython code.

## Dependencies
- `struct` module: Used for unpacking data from byte arrays.
- `time` module: Used for adding delays in the code.
- `_blinx_blinx` module: Required for the `i2c` object used for I2C communication.

## Class

### `SHTC3`
A driver for the SHTC3 temperature and humidity sensor.

#### `__init__()`
Initializes the SHTC3 class instance.

#### `reset()`
Performs a soft reset of the sensor, resetting all settings to their power-on defaults.

#### `sleeping`
Determines the sleep state of the sensor.

#### Setter
- `sleeping(self, sleep_enabled)`: Sets the sleep state of the sensor.

#### Arguments
- `sleep_enabled` (bool): Enables or disables sleep mode.

#### `low_power`
Enables the less accurate low power mode, trading accuracy for power consumption.

#### Setter
- `low_power(self, low_power_enabled)`: Enables or disables low power mode.

#### Arguments
- `low_power_enabled` (bool): Enables or disables low power mode.

#### `relative_humidity()`
Returns the current relative humidity in % rH (percentage).

#### Returns
- `relative_humidity` (float): The current relative humidity.

#### `temperature()`
Returns the current temperature in degrees Celsius.

#### Returns
- `temperature` (float): The current temperature in degrees Celsius.

#### `measurements`
Returns both the temperature and relative humidity measured simultaneously.

#### Returns
- `measurements` (tuple): A tuple containing the temperature and relative humidity measurements.

## Variable

### `_SHTC3_DEFAULT_ADDR`
- Type: Integer
- Description: The default I2C address of the SHTC3 sensor.

### `_SHTC3_NORMAL_MEAS_TFIRST_STRETCH`
- Type: Integer
- Description: Command for normal measurement with temperature first and clock stretch enabled.

### `_SHTC3_LOWPOW_MEAS_TFIRST_STRETCH`
- Type: Integer
- Description: Command for low power measurement with temperature first and clock stretch enabled.

### `_SHTC3_NORMAL_MEAS_HFIRST_STRETCH`
- Type: Integer
- Description: Command for normal measurement with humidity first and clock stretch enabled.

### `_SHTC3_LOWPOW_MEAS_HFIRST_STRETCH`
- Type: Integer
- Description: Command for low power measurement with humidity first and clock stretch enabled.

### `_SHTC3_NORMAL_MEAS_TFIRST`
- Type: Integer
- Description: Command for normal measurement with temperature first and clock stretch disabled.

### `_SHTC3_LOWPOW_MEAS_TFIRST`
- Type: Integer
- Description: Command for low power measurement with temperature first and clock stretch disabled.

### `_SHTC3_NORMAL_MEAS_HFIRST`
- Type: Integer
- Description: Command for normal measurement with humidity first and clock stretch disabled.

### `_SHTC3_LOWPOW_MEAS_HFIRST`
- Type: Integer
- Description: Command for low power measurement with humidity first and clock stretch disabled.

### `_SHTC3_READID`
- Type: Integer
- Description: Command to read the ID register of the SHTC3 sensor.

### `_SHTC3_SOFTRESET`
- Type: Integer
- Description: Command for a soft reset of the SHTC3 sensor.

### `_SHTC3_SLEEP`
- Type: Integer
- Description: Command to enter sleep mode of the SHTC3 sensor.

### `_SHTC3_WAKEUP`
- Type: Integer
- Description: Command to wake up the SHTC3 sensor from sleep mode.

### `_SHTC3_CHIP_ID`
- Type: Integer
- Description: Expected chip ID of the SHTC3 sensor.

## Functions

### `temp_from_raw(t, times_sensors)`
Converts raw temperature data to degrees Celsius.

#### Arguments
- `t` (int): Raw temperature data.
- `times_sensors` (int): Number of sensors.

#### Returns
- Converted temperature value in degrees Celsius.

### `temp_from_raw_default(t)`
Converts raw temperature data to degrees Celsius using default calculation.

#### Arguments
- `t` (int): Raw temperature data.

#### Returns
- Converted temperature value in degrees Celsius.

### `humid_from_raw(h, times_sensors)`
Converts raw humidity data to percentage relative humidity.

#### Arguments
- `h` (int): Raw humidity data.
- `times_sensors` (int): Number of sensors.

#### Returns
- Converted relative humidity value in percentage.

### `humid_from_raw_default(h)`
Converts raw humidity data to percentage relative humidity using default calculation.

#### Arguments
- `h` (int): Raw humidity data.

#### Returns
- Converted relative humidity value in percentage.

### Variable

### `shtc3_sensor`
Instance of the `SHTC3` class representing the SHTC3 sensor.

### `info`
Dictionary containing information about the sensor:
- `'shtc3-temp'`: Temperature measurement information
  - `'function'`: Method to get the temperature measurement
  - `'function_csv'`: Helper function to convert temperature data to a formatted string for CSV output
  - `'size_csv'`: Size of the CSV field for temperature data
  - `'type'`: Type of measurement (input)
  - `'char'`: Character representing the measurement
  - `'more'`: Additional information (empty in this case)
- `'shtc3-humid'`: Humidity measurement information
  - `'function'`: Method to get the humidity measurement
  - `'function_csv'`: Helper function to convert humidity data to a formatted string for CSV output
  - `'size_csv'`: Size of the CSV field for humidity data
  - `'type'`: Type of measurement (input)
  - `'char'`: Character representing the measurement
  - `'more'`: Additional information (empty in this case)

## Usage Example
```python
import _blinx_blinx
import _blinx_shtc3

# Define I2C object and sensor instance
_blinx_blinx.i2c_init()
i2c = _blinx_blinx.i2c
sht = _blinx_shtc3.SHTC3(i2c)

# Read temperature and relative humidity
temperature, relative_humidity = sht.measurements
print("Temperature:", temperature, "°C")
print("Relative Humidity:", relative_humidity, "%")
```