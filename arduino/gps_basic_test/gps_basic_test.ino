#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <Wire.h>
#include <RTClib.h>

// Pin Definitions
#define GPS_RX 0      // GPS Module Receive pin
#define GPS_TX 1      // GPS Module Transmit pin
// RTC uses I2C pins on inventr.io board (PWM rail side):
// SCL -> Pin 18 (SCL)
// SDA -> Pin 17 (SDA)

// Initialize objects
SoftwareSerial GPSSerial(GPS_RX, GPS_TX);  // GPS Serial
TinyGPSPlus gps;                           // GPS parser
RTC_DS3231 rtc;                            // RTC object

// Timing variables
unsigned long lastRTCUpdate = 0;
unsigned long lastGPSCheck = 0;
const unsigned long RTC_INTERVAL = 3000;    // RTC update every 3 seconds
const unsigned long GPS_INTERVAL = 6000;    // GPS check every 6 seconds

// Buffer for timestamp
char timestamp[25];  // YYYY-MM-DD HH:mm:ss format
bool rtcWorking = false;

// Change to true to set RTC time, then back to false and upload again
#define SET_RTC_TIME false

void setup() {
  // Start Serial Monitor
  Serial.begin(9600);
  while (!Serial) delay(100); // Wait for serial console
  
  // Initialize RTC
  rtcWorking = rtc.begin();
  if (rtcWorking) {
    Serial.println("RTC Connected!");
    
    if (SET_RTC_TIME) {
      Serial.println("Setting RTC time from computer...");
      rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
      Serial.println("RTC time set! Please:");
      Serial.println("1. Change SET_RTC_TIME to false");
      Serial.println("2. Upload the sketch again");
      while (1) delay(100); // Stop here
    }
    
    // Check if RTC has lost power
    if (rtc.lostPower()) {
      Serial.println("WARNING: RTC has lost power!");
      Serial.println("Set SET_RTC_TIME to true and upload again");
    }
    
    // Display current RTC time
    DateTime now = rtc.now();
    char curr_time[25];
    sprintf(curr_time, "%04d-%02d-%02d %02d:%02d:%02d",
            now.year(), now.month(), now.day(),
            now.hour(), now.minute(), now.second());
    Serial.print("Current RTC time: ");
    Serial.println(curr_time);
  } else {
    Serial.println("RTC not found - Check pins 17(SDA) and 18(SCL)");
  }
  
  // Start GPS
  GPSSerial.begin(9600);
  Serial.println("GPS Module Started");
  Serial.println("Time stamps every 3s, GPS check every 6s");
}

void loop() {
  // Always read GPS data when available
  while (GPSSerial.available() > 0) {
    gps.encode(GPSSerial.read());
  }

  // Check RTC every 3 seconds
  if (millis() - lastRTCUpdate >= RTC_INTERVAL) {
    printRTCTime();
    lastRTCUpdate = millis();
  }

  // Check GPS every 6 seconds
  if (millis() - lastGPSCheck >= GPS_INTERVAL) {
    checkGPS();
    lastGPSCheck = millis();
  }
}

void printRTCTime() {
  if (!rtcWorking) {
    Serial.println("STATUS,RTC,NOT_CONNECTED");
    return;
  }
  
  DateTime now = rtc.now();
  sprintf(timestamp, "%04d-%02d-%02d %02d:%02d:%02d",
          now.year(), now.month(), now.day(),
          now.hour(), now.minute(), now.second());
  
  // Format: DATA,type,timestamp
  Serial.print("DATA,RTC,");
  Serial.println(timestamp);
}

void checkGPS() {
  if (gps.location.isValid()) {
    // Print in strict CSV format for easy parsing
    // Format: DATA,type,timestamp,lat,lon,alt,sats
    Serial.print("DATA,GPS,");
    if (rtcWorking) {
      Serial.print(timestamp);
    } else {
      Serial.print("NO_RTC");
    }
    Serial.print(",");
    Serial.print(gps.location.lat(), 6);
    Serial.print(",");
    Serial.print(gps.location.lng(), 6);
    Serial.print(",");
    Serial.print(gps.altitude.meters());
    Serial.print(",");
    Serial.println(gps.satellites.value());
  } else {
    Serial.print("GPS: Not Fixed (Satellites: ");
    Serial.print(gps.satellites.value());
    Serial.println(")");
  }
}

