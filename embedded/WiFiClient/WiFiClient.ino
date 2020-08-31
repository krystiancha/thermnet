#include <ESP8266WiFi.h>
#include <Wire.h>

const int CRITICAL = 50;
const int ERROR = 40;
const int WARNING = 30;
const int INFO = 20;
const int DEBUG = 10;
const int NOTSET = 0;
const char LOG_LEVEL_NAMES[] =
    "NOTSET\0   DEBUG\0    INFO\0     WARNING\0  ERROR\0    CRITICAL";

const int LOG_LEVEL = DEBUG;
const int BAUD = 74880;
const int SDA_PIN = 2;
const int SCL_PIN = 0;
const int DEVICE_ADDRESS = 0x76;
const String SSID = "changeme";
const String PASSWORD = "changeme";
const String SERVER_ADDRESS = "192.168.0.10";
const String SERVER_HOST = "thermnet.lan";
const int SERVER_PORT = 80;
const String SHARED_SECRET = "changeme";
const bool ONLINE = true;

byte buffer[8];
uint16_t digT1, digP1;
int16_t digT2, digT3, digP2, digP3, digP4, digP5, digP6, digP7, digP8, digP9,
    digH2, digH4, digH5;
uint8_t digH1, digH3;
int8_t digH6;
int32_t tFine;
WiFiClient client;

void setup() {
  Serial.begin(74880);
  log("BAUD = " + String(BAUD), INFO);

  Wire.begin(SDA_PIN, SCL_PIN);
  log("SDA_PIN = " + String(SDA_PIN), INFO);
  log("SCL_PIN = " + String(SCL_PIN), INFO);
  log("DEVICE_ADDRESS = " + String(DEVICE_ADDRESS), INFO);

  initSensor();

  log("ONLINE = " + String(ONLINE ? "true" : "false"), INFO);
  if (ONLINE) {
    log("SSID = " + String(SSID), INFO);
    log("PASSWORD = " + String(stringToStars(PASSWORD)), INFO);
    log("SERVER_HOST = " + SERVER_HOST, INFO);
    log("SERVER_PORT = " + String(SERVER_PORT), INFO);
    log("SHARED_SECRET = " + String(stringToStars(SHARED_SECRET)), INFO);
    WiFi.begin(SSID, PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
      log("Connecting WiFi...", INFO);
      delay(500);
    }
    log("WiFi connected", INFO);
  }
}

void loop() {
  Wire.beginTransmission(DEVICE_ADDRESS);
  Wire.write(0xF4);
  Wire.write(B00100101); // temperature oversampling x1, pressure oversampling
                         // x1, forced mode
  Wire.write(0xF7);
  Wire.endTransmission();
  Wire.requestFrom(DEVICE_ADDRESS, 8);
  for (int i = 0; Wire.available() && i < 8; ++i) {
    buffer[i] = Wire.read();
  }

  String temperature = temperatureToString(compensateTemperature(
      ((int32_t)buffer[3] << 12) | ((int32_t)buffer[4] << 4) |
      ((int32_t)buffer[5] >> 4)));
  log("Temperature: " + temperature + " °C", INFO);

  String pressure = pressureToString(compensatePressure(
      ((int32_t)buffer[0] << 12) | ((int32_t)buffer[1] << 4) |
      ((int32_t)buffer[2] >> 4)));
  log("Pressure: " + pressure + " hPa", INFO);

  String humidity = humidityToString(compensateHumidity(
      ((int32_t)buffer[6] << 8) | ((int32_t)buffer[7] << 0)));
  log("Humidity: " + humidity + " %", INFO);

  if (ONLINE) {
    log("Connecting to the server...", INFO);
    if (client.connect(SERVER_ADDRESS ? SERVER_ADDRESS : SERVER_HOST, SERVER_PORT)) {
      log("Connected to the server", INFO);

      String body = "{\"temperature\": " + temperature + ", \"pressure\": " + pressure + ", \"humidity\": " + humidity + ", \"secret\": \"" + SHARED_SECRET + "\"}";
      client.println("POST /measurements/ HTTP/1.1");
      client.println("Content-Length: " + String(body.length()));
      client.println("Content-Type: application/json");
      client.println("Host: " + SERVER_HOST);
      client.println("User-Agent: ThermnetClient");
      client.println("");
      client.print(body);
      while (client.connected() || client.available()) {
        if (client.available()) {
          String line = client.readStringUntil('\n');
          if (line == "\r") {
            break;
          }
          log("Server responded: " + line, INFO);
        }
      }
        client.stop();

    } else {
      log("Connection to the server failed", ERROR);
    }
  }

  delay(1 * 1000);
}

void initSensor() {
  int start = 0x88;
  Wire.beginTransmission(DEVICE_ADDRESS);
  Wire.write(0xF2);
  Wire.write(B001); // humidity oversampling x1
  Wire.write(start);
  Wire.endTransmission();
  Wire.requestFrom(DEVICE_ADDRESS, 0xE8 - start);

  digT1 = (uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8); // 88 89
  digT2 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 8A 8B
  digT3 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 8C 8D
  digP1 = (uint16_t)Wire.read() | ((uint16_t)Wire.read() << 8); // 8E 8F
  digP2 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 90 91
  digP3 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 92 93
  digP4 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 94 95
  digP5 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 96 97
  digP6 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 98 99
  digP7 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 9A 9B
  digP8 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 9C 9D
  digP9 = (int16_t)Wire.read() | ((int16_t)Wire.read() << 8);   // 9E 9F
  Wire.read(); // A0
  digH1 = Wire.read(); // A1
  for (int i = 0xA2; i <= 0xE0; ++i) { // A2 -- E0
    Wire.read();
  }
  digH2 = (int16_t) Wire.read() | ((int16_t) Wire.read() << 8); // E1 E2
  digH3 = Wire.read(); // E3
  digH4 = (int16_t) Wire.read() << 4; // E4
  byte var = Wire.read(); // E5
  digH4 |= (int16_t) (var & B00001111);
  digH5 = ((int16_t) Wire.read() << 4) | ((int16_t) (var & B11110000) >> 4); // E6
  digH6 = Wire.read(); // E7

  log("dig_T1 = " + String(digT1), INFO);
  log("dig_T2 = " + String(digT2), INFO);
  log("dig_T3 = " + String(digT3), INFO);
  log("dig_P1 = " + String(digP1), INFO);
  log("dig_P2 = " + String(digP2), INFO);
  log("dig_P3 = " + String(digP3), INFO);
  log("dig_P4 = " + String(digP4), INFO);
  log("dig_P5 = " + String(digP5), INFO);
  log("dig_P6 = " + String(digP6), INFO);
  log("dig_P7 = " + String(digP7), INFO);
  log("dig_P8 = " + String(digP8), INFO);
  log("dig_P9 = " + String(digP9), INFO);
  log("dig_H1 = " + String(digH1), INFO);
  log("dig_H2 = " + String(digH2), INFO);
  log("dig_H3 = " + String(digH3), INFO);
  log("dig_H4 = " + String(digH4), INFO);
  log("dig_H5 = " + String(digH5), INFO);
  log("dig_H6 = " + String(digH6), INFO);
}

int32_t compensateTemperature(int32_t value) {
  int32_t var1, var2;
  var1 = (((value >> 3) - ((int32_t)digT1 << 1)) * ((int32_t)digT2)) >> 11;
  var2 =
      (((((value >> 4) - (int32_t)digT1) * ((value >> 4) - (int32_t)digT1)) >>
        12) *
       ((int32_t)digT3)) >>
      14;
  tFine = var1 + var2;
  return (tFine * 5 + 128) >> 8;
}

uint32_t compensatePressure(int32_t value) {
  int64_t var1, var2, p;
  var1 = ((int64_t)tFine) - 128000;
  var2 = var1 * var1 * (int64_t)digP6;
  var2 = var2 + ((var1 * (int64_t)digP5) << 17);
  var2 = var2 + (((int64_t)digP4) << 35);
  var1 =
      ((var1 * var1 * (int64_t)digP3) >> 8) + ((var1 * (int64_t)digP2) << 12);
  var1 = (((((int64_t)1) << 47) + var1)) * ((int64_t)digP1) >> 33;
  if (var1 == 0) {
    return 0; // avoid exception caused by division by zero
  }
  p = 1048576 - value;
  p = (((p << 31) - var2) * 3125) / var1;
  var1 = (((int64_t)digP9) * (p >> 13) * (p >> 13)) >> 25;
  var2 = (((int64_t)digP8) * p) >> 19;
  p = ((p + var1 + var2) >> 8) + (((int64_t)digP7) << 4);
  return (uint32_t)p;
}

uint32_t compensateHumidity(int32_t value) {
  int32_t var;

  var = tFine - (int32_t)76800;
  var =
      (((((value << 14) - (((int32_t)digH4) << 20) - (((int32_t)digH5) * var)) +
         ((int32_t)16384)) >>
        15) *
       (((((((var * ((int32_t)digH6)) >> 10) *
            (((var * ((int32_t)digH3)) >> 11) + ((int32_t)32768))) >>
           10) +
          ((int32_t)2097152)) *
             ((int32_t)digH2) +
         8192) >>
        14));
  var = (var - (((((var >> 15) * (var >> 15)) >> 7) * ((int32_t)digH1)) >> 4));
  var = (var < 0 ? 0 : var);
  var = (var > 419430400 ? 419430400 : var);

  return var >> 12;
}

String temperatureToString(int32_t temperature) {
  int frac = temperature % 100;
  return String(temperature / 100) + "." + (frac < 10 ? "0" : "") +
         String(frac);
}

String pressureToString(uint32_t pressure) {
  return String((float)pressure / 25600, 3);
}

String humidityToString(uint32_t humidity) {
  return String((float)humidity / 1024, 3);
}

String stringToStars(String s) {
  for (int i = 0; i < s.length(); ++i) {
    s[i] = '*';
  }

  return s;
}

void log(String msg, int level) {
  if (level >= LOG_LEVEL) {
    Serial.print(String(millis()) + ":" + (LOG_LEVEL_NAMES + level) + ":" +
                 msg + "\n");
  }
}
