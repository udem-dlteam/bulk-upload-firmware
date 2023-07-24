# MicroPython Code Documentation - `_blinx_program.py`

The `_blinx_program.py` file contains the main program logic for the MicroPython code.

The code starts by creating tasks for the sensor reader and the web server. Then, it runs the event loop to execute these tasks concurrently.

The sensor reader task periodically reads sensor data and stores it in the `measurements` list. It also handles the averaging of data for different time intervals.

The web server task handles incoming requests and responds with the requested data. It supports two types of encapsulation: NoEncapsulation and PNGEncapsulation. The choice of encapsulation is determined by the request headers.

The main function runs indefinitely, continuously processing sensor data and serving web requests.

This code is designed for a MicroPython environment and may require specific hardware configurations and dependencies to run properly.

## Dependencies

The code has the following dependencies:
- `_blinx_blinx` module as `blinx`
- `_blinx_config` module as `_config`
- `_blinx_wifi` module as `_wifi`
- `_blinx_version` module as `_version`
- `ubinascii` module from MicroPython
- `os` module from MicroPython
- `sys` module from MicroPython
- `time` module from MicroPython
- `struct` module from MicroPython
- `binascii` module from MicroPython
- `uasyncio` module from MicroPython
- `network` module from MicroPython
- `ntptime` module from MicroPython
- `gc` module from MicroPython
- `_blinx_output_sensor` module as `output_sensor_file`
- `_blinx_shtc3` module as `shtc3`
- `_blinx_analog` module as `analog`
- `_blinx_ds1820` module as `ds1820`
- `_blinx_ssd1306` module as `ssd1306`
- `_blinx_font8x12` module as `font`

## Variables

### `safe_fs` - bool
Boolean variable for the activation of the write and remove operations.

### `wlan` - None
Variable to store the WLAN connection information.

### `general_size` - int
The general size value for data.

### `size_data_sensors` - list of int
The size values for data sensors for different data sensors.

### `offset_data` - list of int
The offset values for different data.

### `offset_to_seconds` - list of int
The offset values in seconds for different time intervals.

### `unixtime_servers` - tuple
Containing information about Unix time servers.

### `ntp_servers` - tuple
Containing NTP server addresses.

### `png_overhead` - int
The number of bytes added by PNG encapsulation.

### `import_file_sensors` - list
The list of imported sensor files.

### `input_index_sensors` - list
The index names of the input sensors.

### `input_short_name_sensors` - list
The short names of the input sensors.

### `input_functions_sensors` - list
The functions associated with the input sensors.

### `input_functions_sensors_csv` - list
The CSV functions associated with the input sensors.

### `input_size_sensors_csv` - list
The CSV sizes associated with the input sensors.

### `input_more_sensors` - list
Additional information for the input sensors.

### `type_char_sensors` - list
The character types associated with the sensors.

### `input_true_name` - list
The true names of the input sensors.

### `nsamples` - int
The number of samples.

### `nsensors_input` - int
The number of input sensors.

### `nsensors_input_use` - int
The number of input sensors in use.

### `input_pin_sensors` - list
The input pin numbers of the sensors.

### `input_type_sensors` - list
The input types of the sensors.

### `measurement_time` - variable
The measurement time.

### `lo` - list
The list of low values.

### `hi` - list
The list of high values.

### `done_one` - list
The list indicating if we have save one at least one data for each time.

### `bytes_per_measurement` - int
The number of bytes use for each measurement.

### `size_bytearray` - list
The list of sizes for the bytearray.

### `measurements` - list
The list of measurements.

### `input_size_sensors_csv` - list
The CSV sizes of the input sensors.

### `affichage_sensors_list` - list
The list of sensors to be displayed.

### `csv_header` - bytes
The CSV header.

## Functions

### `safe_to_modify(filename)`
Function to check if the filename is safe to modify by comparing it with certain conditions.

#### Arguments:
- `filename` (str): The name of the file to check.

#### Return:
A boolean value indicating whether the filename is safe to modify.

### `get_time()`
Function to get the current time.

#### Return:
The current time in seconds.

### `screen_init()`
Function to initialize the screen output by creating an instance of the `SSD1306_I2C` class.

### `screen_write(line, text, start_x, fg=1)`
Function to writes the specified text on the screen at the given line and starting position.

#### Arguments:
- `line` (int): The line number on the screen to write the text.
- `text` (str): The text to be written on the screen.
- `start_x` (int): The starting position of the text on the X-axis.
- `fg` (int, optional): The foreground color of the text. Defaults to 1.

### `screen_erase()`
Function to erase the screen.

### `write(text, w, h, start_x, start_y)`
Function to write text on the screen with custom settings such as character width, height, and starting position.

#### Arguments:
- `text` (str): The text to be written on the screen.
- `w` (int): The width of each character.
- `h` (int): The height of each character.
- `start_x` (int): The starting position of the text on the X-axis.
- `start_y` (int): The starting position of the text on the Y-axis.

### `screen_cycle_count` - int
Variable to keep track of the screen cycle count for displaying different screens or instructions.

### `screen_instructions_count` - int
Variable to keep track of the screen instructions count for displaying different instructions.

### `write_config_id(data=[])`
Function to write the configuration ID on the screen and additional data on the screen.

#### Arguments:
- `data` (list, optional): Additional data to display on the screen. Defaults to an empty list.

### `wlan_start_connect()`
Function to start the WLAN connection by creating a WLAN object and connecting to the specified SSID and password.

### `wlan_connect_loop(wl)`
Asynchronous function to handle the WLAN connection loop and waits for the connection to be established.

#### Arguments:
- `wl` (network.WLAN): The WLAN object for the connection.

### `wlan_disconnect()`
Function to disconnect the current WLAN connection.

### Class : `AsyncWriter`
Class representing an asynchronous writer.

### Class : `AsyncReader`
Class representing an asynchronous reader.

### `async def web_server()`
This function represents the main web server functionality. It handles client connections and processes HTTP requests.

#### `async def handle_client_connection(rstream, wstream)`
This function handles an individual client connection and processes the client's request.

##### Arguments
- `rstream`: The read stream for the client connection.
- `wstream`: The write stream for the client connection.

##### `async def register(doc, q, content, encapsulation, wstream)`
This function handles the registration process for different types of requests. This is for the API of blinx.

The `register` function contains a series of conditional statements that check the type of request you did to the API and perform the appropriate actions. Here are some of the supported request types:
- Write a file: If the request begins with `write=`, the function extracts the file name, content, and format from the request and writes the content to the specified file using the specified format.
- Read a file: If the request begins with `read=`, the function reads the specified file and sends its content back to the client.
- Remove a file: If the request begins with `remove=`, the function deletes the specified file from the file system.
- Get the list of files: If the request begins with `ls=`, the function retrieves the list of files in the specified directory and sends it back to the client.
- Get the version of blinx: If the request begins with `version=`, the function retrieves the version information and sends it back to the client.
- Stop data collection: If the request begins with `sensors_stop=`, the function stops the data collection process.
- Configure a sensor: If the request begins with `config=`, the function configures the specified sensor based on the information provided in the request.
- Change output sensor: If the request begins with `content=` or `output=`, the function changes the output configuration of a sensor based on the information provided in the request.

If none of the above conditions are met, the function falls back to a default behavior and invokes the `main_page` function to handle the request.

###### Arguments
- `doc`: The document containing the request information.
- `q`: The starting index of the request within the document.
- `content`: The content associated with the request.
- `encapsulation`: The encapsulation object for sending the response.
- `wstream`: The write stream for the client connection.

##### `async def registerGetSensor(doc, q)`
This function handles the retrieval of sensor information when requesting data in CSV format.

###### Arguments
- `doc`: The document containing the request information.
- `q`: The starting index of the request within the document.

###### Returns
- `n`: The number of data points requested.
- `times_sensors`: The time interval for the sensor data.

#### Example Usage
Here are some examples of requests that can be made to the web server:

1. File Write Request:
   - Path: "/"
   - Parameters:
     - `write`: Specifies the file to write.
     - `content`: Specifies the content to write.
     - `format`: Specifies the file format (optional).
   - Purpose: Writes the provided content to the specified file.
   - Example: `http://<server_ip>/?write=<file_name>&content=<base64_encoded_content>&format=<file_format>`

2. File Read Request:
   - Path: "/"
   - Parameters:
     - `read`: Specifies the file to read.
     - `pos`: Specifies the position to start reading from (optional).
   - Purpose: Reads the contents of the specified file.
   - Example: `http://<server_ip>/?read=<file_name>&pos=<position>`

3. File Removal Request:
   - Path: "/"
   - Parameters:
     - `remove`: Specifies the file to remove.
   - Purpose: Removes the specified file from the server.
   - Example: `http://<server_ip>/?remove=<file_name>`

4. File List Request:
   - Path: "/"
   - Parameters:
     - `ls`: Specifies the directory to list files from.
   - Purpose: Retrieves a list of files in the specified directory.
   - Example: `http://<server_ip>/?ls=<directory>`

5. Version Request:
   - Path: "/"
   - Parameters:
     - `version`: Retrieves the version of the server.
   - Purpose: Returns the version information of the server.
   - Example: `http://<server_ip>/?version`

6. Sensors Stop Request:
   - Path: "/"
   - Parameters:
     - `sensors_stop`: Stops the data collection from sensors.
   - Purpose: Stops the data collection process from the sensors.
   - Example: `http://<server_ip>/?sensors_stop`

7. Sensor Configuration Request:
   - Path: "/"
   - Parameters:
     - `config`: Configures the sensor settings.
   - Purpose: Configures the sensor settings based on the provided parameters.
   - Example: `http://<server_ip>/?config=<sensor_settings>`

8. Output/Content Change Request:
   - Path: "/"
   - Parameters:
     - `output` or `content`: Specifies the output sensor or content to change.
   - Purpose: Changes the output sensor settings or content.
   - Example: `http://<server_ip>/?output=<sensor_settings>` or `http://<server_ip>/?content=<base64_encoded_content>`

9.  Register Get Sensor Request (CSV Data):
   - Path: "/<sensor_name>.csv"
   - Parameters:
     - `n`: Specifies the number of data points to retrieve (optional).
     - `delta`: Specifies the time interval between data points (optional).
   - Purpose: Retrieves sensor data in CSV format.
   - Example: `http://<server_ip>/<sensor_name>.csv?n=<data_points>&delta=<time_interval>`

10. `favicon.ico``:
   - Path: "/favicon.ico"
   - Purpose: Returns a "Bad Request" error response.
   - Example: `http://<server_ip>/favicon.ico`

11. Unknown Path Request:
   - Path: Any path other than "/favicon.ico" or "/?<know_get_argument>" or "/<sensor_name>.csv"
   - Purpose: We go to the CodeBoot website.
   - Example: `http://<server_ip>/unknown_path`

Please note that the examples provided assume the `<server_ip>` placeholder represents the actual IP address or the `name.local` (with `name` the name of the Blinx, for example : `BLINX000.local`) of the Blinx. Additionally, make sure to replace `<sensor_name>`, `<file_name>`, `<file_format>`, `<directory>`, `<sensor_settings>`, `<base64_encoded_content>`, `<data_points>`, and `<time_interval>` with the relevant values for your specific use case.

### `async def settime_from_unixtime_servers()`
This function sets the current time by retrieving the time from a Unix time server.

### `def settime(t)`
This function sets the system time using the provided Unix timestamp.

#### Arguments
- `t`: The Unix timestamp to set as the system time.

### `def sync_ntptime()`
This function synchronizes the system time using NTP (Network Time Protocol) servers.

### `async def main_page(encapsulation)`
This function generates the main HTML page for the web server.

#### Arguments
- `encapsulation`: The encapsulation object for sending the response.

### Class: NoEncapsulation
This class is responsible for handling data without encapsulation.

#### Method: `__init__(self, wstream)`
Constructor method for the NoEncapsulation class.

##### Arguments
- `wstream`: The writable stream to which the data will be written.

#### Method: `start(self, type, nbytes)`
Starts the data transmission.

##### Arguments
- `type`: The type of the content.
- `nbytes`: The number of bytes to be transmitted.

#### Method: `add(self, data)`
Adds data to the transmission.

##### Arguments
- `data`: The data to be added.

#### Method: `end(self)`
Ends the data transmission.

### Class: PNGEncapsulation
This class handles data encapsulation in PNG format.

#### Method: `__init__(self, wstream)`
Constructor method for the PNGEncapsulation class.

##### Arguments
- `wstream`: The writable stream to which the data will be written.

#### Method: `start(self, type, nbytes)`
Starts the PNG encapsulation.

##### Arguments
- `type`: The type of the content.
- `nbytes`: The number of bytes to be encapsulated.

#### Method: `add(self, data)`
Adds data to the encapsulation.

##### Arguments
- `data`: The data to be added.

#### Method: `end(self)`
Ends the PNG encapsulation.

### `modify_port_input(port, name, save_output_sensors_csv, get_save_output_sensors)`
Modifies the input port type for a given sensor.

#### Arguments
- `port`: The port number.
- `name`: The name of the sensor.
- `save_output_sensors_csv`: Function to save the output sensors in CSV format.
- `get_save_output_sensors`: Function to get the saved output sensors.

### `sensor_reader()`
Reads sensor data at regular intervals. Here's an overview of its functionality:
1. It calculates the remaining time until the next second boundary and sleeps for that duration.
2. If there are no sensors configured, it skips to the next iteration.
3. It checks if a full cycle of sensor readings has been completed.
4. It calculates the current time interval.
5. It determines if there is an additional delta time interval to process.
6. It checks if DS1820 temperature sensors are being used and performs a temperature conversion.
7. It clears any previous output sensor values.
8. It retrieves the current measurement time.
9. It collects data from the sensors.
10. It averages the collected sensor data.
11. If DS1820 sensors are being used, it waits for the required conversion time and reads the temperature values.
12. It updates the index for storing the collected data.
13. It stores the collected sensor data in the measurements array.
14. It updates the index for retrieving the stored data.
15. If there is an additional delta time interval to process, it performs averaging calculations.
16. It checks if data needs to be displayed on the screen.
17. It performs garbage collection.

### `get_sensor_analog_ds1820(n,m)`
Gets the information for the analog and ds1820 sensors.

#### Arguments
- `n`: The first index.
- `m`: The second index.

### `get_time_sensors(modulo)`
Gets the time for the sensors.

#### Arguments
- `modulo`: The modulo value.

### `moyenneData(toDo_interval)`
Calculates the average data for the next delta time interval. Here's an overview of its functionality:

1. It receives the `toDo_interval` parameter, which indicates the delta time interval for which to calculate the median.
2. It calculates the difference between the current delta time interval and the previous delta time interval.
3. It initializes variables and checks the completion status of the previous delta time interval.
4. It updates the index for storing the calculated median values.
5. It retrieves the last index of the previous delta time interval.
6. It checks if there is a wraparound condition, and if so, calculates the median values accordingly.
7. It iterates over the relevant sensor data and calculates the sum of the values for each sensor.
8. It calculates the number of valid measurements for the median calculation.
9. It calculates the median values for each sensor and stores them in the measurements array for the current delta time interval.
10. It updates the index for retrieving the stored data in the current delta time interval.
11. If there is a wraparound condition, it updates the index for the current delta time interval accordingly.

#### Arguments
- `toDo_interval`: The delta time value.


### `measurements_as_csv(encapsulation, name, n, times_sensors)`
Gets the measurements as CSV format (Comma-Separated Values) representation of sensor measurements. Here's an overview of its functionality:

1. It converts the `times_sensors` string into an index representing the corresponding delta time interval.
2. It initializes variables and determines the size of the CSV header based on the selected sensors and their respective data sizes.
3. It updates the list of sensors to be displayed in the CSV based on the selected sensors.
4. It calculates the available number of measurements within the selected delta time interval.
5. It ensures that the desired number of measurements does not exceed the available number of measurements.
6. It starts the encapsulation object with the CSV content type and the total length of the CSV data.
7. It adds the CSV header to the encapsulation object.
8. It iterates through the selected number of measurements.
9.  It calculates the measurement time for each measurement based on the selected delta time interval.
10. It retrieves the corresponding sensor data for each measurement and appends it to the CSV row.
11. It converts the CSV row to bytes and adds it to the encapsulation object.
12. Once all measurements have been processed, it ends the encapsulation process.

#### Arguments
- `encapsulation`: The encapsulation method.
- `name`: The name of the measurements.
- `n`: The number of measurements.
- `times_sensors`: The time interval for measurements.

### `main()`
The main function of the code.

#### Steps
1. Create a task for the sensor reader.
2. Create a task for the web server.
3. Run the event loop.

