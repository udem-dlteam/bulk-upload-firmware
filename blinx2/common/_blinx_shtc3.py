from struct import unpack_from
import time
from _blinx_blinx import i2c

_SHTC3_DEFAULT_ADDR = 0x70  # SHTC3 I2C Address
_SHTC3_NORMAL_MEAS_TFIRST_STRETCH = (
    0x7CA2  # Normal measurement, temp first with Clock Stretch Enabled
)
_SHTC3_LOWPOW_MEAS_TFIRST_STRETCH = (
    0x6458  # Low power measurement, temp first with Clock Stretch Enabled
)
_SHTC3_NORMAL_MEAS_HFIRST_STRETCH = (
    0x5C24  # Normal measurement, hum first with Clock Stretch Enabled
)
_SHTC3_LOWPOW_MEAS_HFIRST_STRETCH = (
    0x44DE  # Low power measurement, hum first with Clock Stretch Enabled
)

_SHTC3_NORMAL_MEAS_TFIRST = (
    0x7866  # Normal measurement, temp first with Clock Stretch disabled
)
_SHTC3_LOWPOW_MEAS_TFIRST = (
    0x609C  # Low power measurement, temp first with Clock Stretch disabled
)
_SHTC3_NORMAL_MEAS_HFIRST = (
    0x58E0  # Normal measurement, hum first with Clock Stretch disabled
)
_SHTC3_LOWPOW_MEAS_HFIRST = (
    0x401A  # Low power measurement, hum first with Clock Stretch disabled
)

_SHTC3_READID = 0xEFC8  # Read Out of ID Register
_SHTC3_SOFTRESET = 0x805D  # Soft Reset
_SHTC3_SLEEP = 0xB098  # Enter sleep mode
_SHTC3_WAKEUP = 0x3517  # Wakeup mode
_SHTC3_CHIP_ID = 0x807


class SHTC3:
    '''
    A driver for the SHTC3 temperature and humidity sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the SHTC3 is connected to.

    **Quickstart: Importing and using the SHTC3 temperature and humidity sensor**

        Here is an example of using the :class:`SHTC3`.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            import adafruit_shtc3

        Once this is done, you can define your `board.I2C` object and define your sensor

        .. code-block:: python

            i2c = board.I2C()   # uses board.SCL and board.SDA
            sht = adafruit_shtc3.SHTC3(i2c)

        Now you have access to the temperature and humidity using the :attr:`measurements`.
        it will return a tuple with the :attr:`temperature` and :attr:`relative_humidity`
        measurements

        .. code-block:: python

            temperature, relative_humidity = sht.measurements

    '''

    def __init__(self):
        self._addr = _SHTC3_DEFAULT_ADDR

        self._buffer = bytearray(6)
        self.low_power = False
        self.sleeping = False
        self.reset()
#        self._chip_id = self._get_chip_id()
#        if self._chip_id != _SHTC3_CHIP_ID:
#            raise RuntimeError('Failed to find an SHTC3 sensor - check your wiring!')

    def _write_command(self, command):
        '''helper function to write a command to the i2c device'''
        self._buffer[0] = command >> 8
        self._buffer[1] = command & 0xFF

        i2c.writeto(self._addr, self._buffer[0:2])

    def _get_chip_id(self):  #   readCommand(SHTC3_READID, data, 3);
        '''Determines the chip id of the sensor'''
        self._write_command(_SHTC3_READID)
        time.sleep(0.001)

        return unpack_from('>H', i2c.readfrom(self._addr, 2))[0] & 0x083F

    def reset(self):
        '''Perform a soft reset of the sensor, resetting all settings to their power-on defaults'''
        self.sleeping = False
        self._write_command(_SHTC3_SOFTRESET)

        time.sleep(0.001)

    @property
    def sleeping(self):
        '''Determines the sleep state of the sensor'''
        return self._cached_sleep

    @sleeping.setter
    def sleeping(self, sleep_enabled):
        try:
            if sleep_enabled:
                self._write_command(_SHTC3_SLEEP)
            else:
                self._write_command(_SHTC3_WAKEUP)
            time.sleep(0.001)
            self._cached_sleep = sleep_enabled
        except OSError:
            pass

    # lowPowerMode(bool readmode) { _lpMode = readmode

    @property
    def low_power(self):
        '''Enables the less accurate low power mode, trading accuracy for power consumption'''
        return self._low_power

    @low_power.setter
    def low_power(self, low_power_enabled):
        self._low_power = low_power_enabled

    #@property
    def relative_humidity(self):
        '''The current relative humidity in % rH. This is a value from 0-100%.'''
        return self.measurements[1]

    #@property
    def temperature(self):
        '''The current temperature in degrees Celsius'''
        return self.measurements[0]

    @property
    def measurements(self):
        '''both `temperature` and `relative_humidity`, read simultaneously'''

        self.sleeping = False

        try:

            # send correct command for the current power state
            if self.low_power:
                self._write_command(_SHTC3_LOWPOW_MEAS_TFIRST)
                time.sleep(0.001)
            else:
                self._write_command(_SHTC3_NORMAL_MEAS_TFIRST)
                time.sleep(0.013)

            # self._buffer = bytearray(6)
            # read the measured data into our buffer

            i2c.readfrom_into(self._addr, self._buffer)

        except OSError:
            return (0, 0)

        # separate the read data
        temp_data = self._buffer[0:2]
        temp_crc = self._buffer[2]
        humidity_data = self._buffer[3:5]
        humidity_crc = self._buffer[5]

        # check CRC of bytes
        if temp_crc != self._crc8(temp_data) or humidity_crc != self._crc8(humidity_data):
            return (0, 0)

        # decode data into human values:
        # convert bytes into 16-bit signed integer
        # convert the LSB value to a human value according to the datasheet
        raw_temp = unpack_from('>H', temp_data)[0]

        # repeat above steps for humidity data
        raw_humidity = unpack_from('>H', humidity_data)[0]

        self.sleeping = True

        return (raw_temp, raw_humidity)

    ## CRC-8 formula from page 14 of SHTC3 datasheet
    # https://media.digikey.com/pdf/Data%20Sheets/Sensirion%20PDFs/HT_DS_SHTC3_D1.pdf
    # Test data [0xBE, 0xEF] should yield 0x92

    @staticmethod
    def _crc8(buffer):
        '''verify the crc8 checksum'''
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits

def temp_from_raw(t, times_sensors):
    return '%5.1f' % (temp_from_raw_default(t) / 100)
def temp_from_raw_default(t):
    return ((4375 * t) >> 14) - 4500  # from spec sheet
#    return ((4375 * t) >> 14) - 4800

def humid_from_raw(h, times_sensors):
    return '%5.1f' % (humid_from_raw_default(h) / 100)
def humid_from_raw_default(h):
    return (625 * h) >> 12


# information on the sensor
shtc3_sensor = SHTC3()
info = {
    'shtc3-temp' : {
        'function' : shtc3_sensor.temperature,
        'function_csv' : temp_from_raw,
        'size_csv' : 5,
        'type' : 'in',
        'char' : '',
        'more' : []
        },
    'shtc3-humid' : {
        'function' : shtc3_sensor.relative_humidity,
        'function_csv' : humid_from_raw,
        'size_csv' : 5,
        'type' : 'in',
        'char' : '',
        'more' : []
        }
}
