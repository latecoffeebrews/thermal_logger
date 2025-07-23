# Arduino Requirements

## Required Libraries
1. TinyGPS++ (for GPS module)
2. RTClib (for DS3231)
3. ArduinoJson (for JSON formatting)
4. SoftwareSerial (included with Arduino)

## Hardware Connections

### GPS Module (GY-GPS6MV2)
- VCC -> Arduino 5V
- GND -> Arduino GND
- RX  -> Arduino Digital Pin 3 (GPS_TX)
- TX  -> Arduino Digital Pin 4 (GPS_RX)

### RTC Module (DS3231)
- VCC -> Arduino 5V
- GND -> Arduino GND
- SDA -> Arduino A4 (SDA)
- SCL -> Arduino A5 (SCL)

### HC-12 Module
- VCC -> Arduino 5V
- GND -> Arduino GND
- RX  -> Arduino Digital Pin 5 (HC12_TX)
- TX  -> Arduino Digital Pin 6 (HC12_RX)
- SET -> Arduino Digital Pin 7 (HC12_SET)

## Installation Steps
1. Open Arduino IDE
2. Install required libraries through Library Manager:
   - TinyGPSPlus by Mikal Hart
   - RTClib by Adafruit
   - ArduinoJson by Benoit Blanchon
3. Copy the code from gps_rtc_transmitter.ino
4. Upload to your Arduino

## Initial Setup
1. When first uploading, uncomment the RTC time setting line:
   ```cpp
   rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
   ```
2. Upload the code
3. Comment out the line again and upload once more

## Features
- Automatically configures HC-12 to Channel 6
- Sends GPS and timestamp data every 10 seconds
- Shows "Connecting" message when GPS signal is not available
- Uses JSON format for data transmission
- Includes satellite count and signal quality monitoring
