# MicroPython Code Documentation - _blinx_ssd1306.py

This code provides a MicroPython driver for the SSD1306 OLED display module with support for both I2C and SPI interfaces.

## Dependencies
- `micropython` module from MicroPython
  - `const` classe from the `machine` module
- `framebuf` module from MicroPython

## Class

### SSD1306
This class represents the SSD1306 OLED display and inherits from the `framebuf.FrameBuffer` class.

#### Function

##### `__init__(self, width, height, external_vcc)`
Initialize the SSD1306 display.

###### Arguments
- `width` (integer): The width of the display in pixels.
- `height` (integer): The height of the display in pixels.
- `external_vcc` (boolean): Flag indicating whether external VCC is used.

##### `init_display(self)`
Initialize the display with the necessary settings and configuration.

##### `poweroff(self)`
Turn off the display.

##### `poweron(self)`
Turn on the display.

##### `contrast(self, contrast)`
Set the contrast level of the display.

###### Arguments
- `contrast` (integer): The contrast level to set.

##### `invert(self, invert)`
Invert the display.

###### Arguments
- `invert` (boolean): Flag indicating whether to invert the display.

##### `show(self)`
Update the display with the contents of the buffer.

#### Variable
- `width` (integer): The width of the display in pixels.
- `height` (integer): The height of the display in pixels.
- `external_vcc` (boolean): Flag indicating whether external VCC is used.
- `pages` (integer): The number of display pages.
- `buffer` (bytearray): The buffer for storing display data.

### SSD1306_I2C
This class represents the SSD1306 OLED display using the I2C interface and inherits from the `SSD1306` class.

#### Function

##### `__init__(self, width, height, i2c, addr=0x3C, external_vcc=False)`
Initialize the SSD1306 display using the I2C interface.

###### Arguments
- `width` (integer): The width of the display in pixels.
- `height` (integer): The height of the display in pixels.
- `i2c` (I2C): The I2C bus object.
- `addr` (integer): The I2C address of the display (default: 0x3C).
- `external_vcc` (boolean): Flag indicating whether external VCC is used (default: False).

##### `write_cmd(self, cmd)`
Write a command to the SSD1306 display via I2C.

###### Arguments
- `cmd` (integer): The command to write.

##### `write_data(self, buf)`
Write data to the SSD1306 display via I2C.

###### Arguments
- `buf` (bytearray): The data to write.


### SSD1306_SPI
This class represents the SSD1306 OLED display using the SPI interface and inherits from the `SSD1306` class.

#### Function

##### `__init__(self, width, height, spi, dc, res, cs, external_vcc=False)`
Initialize the SSD1306 display using the SPI interface.

###### Arguments
- `width` (integer): The width of the display in pixels.
- `height` (integer): The height of the display in pixels.
- `spi` (SPI): The SPI bus object.
- `dc` (Pin): The data/command pin.
- `res` (Pin): The reset pin.
- `cs` (Pin): The chip select pin.
- `external_vcc` (boolean): Flag indicating whether external VCC is used (default: False).

##### `write_cmd(self, cmd)`
Write a command to the SSD1306 display via SPI.

###### Arguments
- `cmd` (integer): The command to write.


##### `write_data(self, buf)`
Write data to the SSD1306 display via SPI.

###### Arguments
- `buf` (bytearray): The data to write.

## Variables
- `SET_CONTRAST` (integer): Register definition for setting the contrast.
- `SET_ENTIRE_ON` (integer): Register definition for enabling entire display on mode.
- `SET_NORM_INV` (integer): Register definition for setting normal/inverse display mode.
- `SET_DISP` (integer): Register definition for turning the display on/off.
- `SET_MEM_ADDR` (integer): Register definition for setting the memory addressing mode.
- `SET_COL_ADDR` (integer): Register definition for setting the column address.
- `SET_PAGE_ADDR` (integer): Register definition for setting the page address.
- `SET_DISP_START_LINE` (integer): Register definition for setting the display start line.
- `SET_SEG_REMAP` (integer): Register definition for setting the segment remap.
- `SET_MUX_RATIO` (integer): Register definition for setting the multiplex ratio.
- `SET_COM_OUT_DIR` (integer): Register definition for setting the COM output direction.
- `SET_DISP_OFFSET` (integer): Register definition for setting the display offset.
- `SET_COM_PIN_CFG` (integer): Register definition for setting the COM pin configuration.
- `SET_DISP_CLK_DIV` (integer): Register definition for setting the display clock divide ratio/oscillator frequency.
- `SET_PRECHARGE` (integer): Register definition for setting the pre-charge period.
- `SET_VCOM_DESEL` (integer): Register definition for setting the VCOM deselect level.
- `SET_CHARGE_PUMP` (integer): Register definition for setting the charge pump.
- `framebuf.MONO_VLSB` (constant): Constant value for the framebuf format.

## Example Usage

```python
# Import the required libraries
from machine import I2C, SPI, Pin
import _blinx_ssd1306

# I2C interface example
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
display = _blinx_ssd1306.SSD1306_I2C(128, 64, i2c)
display.fill(0)
display.text("Hello, world!", 0, 0, 1)
display.show()

# SPI interface example
spi = SPI(1, baudrate=8000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
dc = Pin(16, Pin.OUT)
res = Pin(17, Pin.OUT)
cs = Pin(5, Pin.OUT)
display = _blinx_ssd1306.SSD1306_SPI(128, 64, spi, dc, res, cs)
display.fill(0)
display.text("Hello, world!", 0, 0, 1)
display.show()
```

Note: Make sure to adjust the I2C interface, SPI interface and pin configurations according to your hardware setup.
