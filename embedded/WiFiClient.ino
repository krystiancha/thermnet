#include <ESP8266WiFi.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <TZ.h>
#include <sntp.h>
#include <time.h>

DeviceAddress sensorAddress = {0x28, 0xEA, 0x28, 0xED, 0xB, 0x0, 0x0, 0x2B};
const int resolution = 12;

String ssid = "";
String password = "";

String serverHost = "thermnet.ken.krystianch.com";

OneWire oneWire(2);
DallasTemperature sensors(&oneWire);

const char *x509CA PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
MIIFcTCCBFmgAwIBAgISA8BXEJ2zdJ64bAIWs51JE1GtMA0GCSqGSIb3DQEBCwUA
MEoxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MSMwIQYDVQQD
ExpMZXQncyBFbmNyeXB0IEF1dGhvcml0eSBYMzAeFw0yMDA1MTAxMTE4NDBaFw0y
MDA4MDgxMTE4NDBaMB0xGzAZBgNVBAMTEmtlbi5rcnlzdGlhbmNoLmNvbTCCASIw
DQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAKa9FievNQjCBOT0kxfgogo6kVy3
P9/+ka/4U8SvsHMGTPtziCcBtO9nLs0LcPcvETDodMsjHD7Z8NMFA6nkjXZqtKcj
yqRq5FymBMSwpF0egftMw4mMAprQOUeFZapK4KQg9Ca7KHs/6BYLlSxO9/jRPiM0
8rWq2VWcghWkUj9Pglk55jFct2UWbK9esLLDeso22aibCo72wP9bRIquVYQ39kjB
TbjYkooefD3tOzwDo4T2uL4ZtEQg9yvbV6HQh4T3dECa7rAFZdiRNXCr7RLw1Q2Q
kWyjR1dd0dEddXg4DF8PSTPTngBOfHc+1Yu1SlFXqvZH/MmFkamOPbDZVWkCAwEA
AaOCAnwwggJ4MA4GA1UdDwEB/wQEAwIFoDAdBgNVHSUEFjAUBggrBgEFBQcDAQYI
KwYBBQUHAwIwDAYDVR0TAQH/BAIwADAdBgNVHQ4EFgQUs66L7QiD1jDA2duPCDm6
M6LDQbcwHwYDVR0jBBgwFoAUqEpqYwR93brm0Tm3pkVl7/Oo7KEwbwYIKwYBBQUH
AQEEYzBhMC4GCCsGAQUFBzABhiJodHRwOi8vb2NzcC5pbnQteDMubGV0c2VuY3J5
cHQub3JnMC8GCCsGAQUFBzAChiNodHRwOi8vY2VydC5pbnQteDMubGV0c2VuY3J5
cHQub3JnLzAzBgNVHREELDAqghQqLmtlbi5rcnlzdGlhbmNoLmNvbYISa2VuLmty
eXN0aWFuY2guY29tMEwGA1UdIARFMEMwCAYGZ4EMAQIBMDcGCysGAQQBgt8TAQEB
MCgwJgYIKwYBBQUHAgEWGmh0dHA6Ly9jcHMubGV0c2VuY3J5cHQub3JnMIIBAwYK
KwYBBAHWeQIEAgSB9ASB8QDvAHUA5xLysDd+GmL7jskMYYTx6ns3y1YdESZb8+Dz
S/JBVG4AAAFx/oXnoQAABAMARjBEAiA18Sy7fDcYn0ygpN9UdhsMGSIxK6OfomOa
TkrFHOU2KwIgSwcKMI0Sb/hW2G0ZhCLfGq21SKDV3tUNK2/084qj6vQAdgAHt1wb
5X1o//Gwxh0jFce65ld8V5S3au68YToaadOiHAAAAXH+hefOAAAEAwBHMEUCIQDq
UPm82dDAeiGXdjo6kxp2XNRAb5u19tuJjDsFvyEHZwIgGb3TdJ8gnLWDEXsVnO7G
L4RdJ6nGLFNsg6VDGtMUNXUwDQYJKoZIhvcNAQELBQADggEBADU+i3XE0wL7H2nq
fCSD5vv+N+Tfsr2mot4EvrIlipHpDABkDybpHa1BvuJJrZIWEVhrH6hiCs7iCOo9
wI5fwaBoXgRsvGY96EeJ7pyBmA5hlIwlvanSn4Ea0uBWvU6s8VA7Gq2Eezx75f4O
KIpGPyP7f0tJNA2zVSev1SXva8zh9J0sb14qGuISvIeSxKOnldnMN4h4I4iI+i/g
fJFlhHRW6MwQ7UbUXV8ga0zkROYo+151NoGxjGY6tlRMnzxJ0TeIObj1kxKa+0cV
zSAegJFy7FbzbbMG5pGWNQXpRvhnOt73V/KEXaUreU3534mR0nk3wdfaNDN6cTX8
J6uUFts=
-----END CERTIFICATE-----
)EOF";
BearSSL::X509List x509(x509CA);

void log(String msg, bool time = true, bool newline = true);
String addressToString(DeviceAddress address);
String stringToStars(String s);

void setup()
{
  Serial.begin(74880);

  log("");
  log("Configuration:");
  log("sensorAddress = " + addressToString(sensorAddress));
  log("resolution = " + String(resolution));
  log("ssid = " + ssid);
  log("password = " + stringToStars(password));

  sensors.begin();
  const int sensorCount = sensors.getDeviceCount();
  log("Sensor count: " + String(sensorCount));
  for (int i = 0; i < sensorCount; ++i) {
    DeviceAddress address;
    if (!sensors.getAddress(address, i)) {
      log("Sensor " + String(i) + ": unknown");
      continue;
    }
    log("Sensor " + String(i) + " address: " + addressToString(address));
  }

  sensors.setResolution(sensorAddress, resolution);
  sensors.requestTemperaturesByAddress(sensorAddress);
  float temperature = sensors.getTempC(sensorAddress);
  log("Configured sensor temperature: " + String(temperature, 2) + "°C");

  log("Connecting WiFi", false);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    log(".", false, false);
    delay(500);
  }
  log(" connected", true, false);

  configTime(TZ_Europe_Warsaw, "pool.ntp.org");
}


void loop()
{
  BearSSL::WiFiClientSecure client;
  client.setTrustAnchors(&x509);
//  client.setInsecure();

  if (!client.connect(serverHost, 443)) {
    log("Connection failed: ", false);
    char error[128];
    client.getLastSSLError(error, 128);
    log(String(error), true, false);
    return;
  }
  
  log("Connected, ", false);
  unsigned t = time(NULL);
  sensors.requestTemperaturesByAddress(sensorAddress);
  float temperature = sensors.getTempC(sensorAddress);
  log("temp. " + String(temperature, 2) + "°C ", false, false);

  String body = 
    "{\r\n"
    "\t\"data\": " + String(temperature, 4) + ",\r\n"
    "\t\"key\": \"tE3M0W1yXH8gGbx4rWGTQt8pQZX9lAx1EZAAK7ttxPdC6LKOY1W01tVMNTuymCdb\",\r\n"
    "\t\"time\": " + String(t) + "\r\n"
    "}\r\n";
  
  client.println("POST /measurements/ HTTP/1.1");
//  client.println("Accept: application/json, */*;q=0.5");
  client.println("Content-Length: " + String(body.length()));
  client.println("Content-Type: application/json");
  client.println("Host: thermnet.ken.krystianch.com");
  client.println("User-Agent: ThermnetClient");
  client.println("");
  client.print(body);
  
  log("sent ", false, false);
  log("at " + String(t) + " ", false, false);

      while (client.connected() || client.available())
    {
      if (client.available())
      {
        String line = client.readStringUntil('\n');
        if (line == "\r") {
          break;
        }
      }
    }
  
  client.stop();
  log("and disconnected", true, false);
}

void log(String msg, bool newline, bool time) {
  Serial.print((time ? String(millis()) + ": " : "") + msg + (newline ? "\n" : ""));
}

String addressToString(DeviceAddress address) {
  String s = "{";
  for (int i = 0; i < 8; ++i) {
    s += "0x";
    s += String(address[i], HEX);
    if (i != 7) {
      s += ", ";
    }
  }
  s += "}";

  return s;
}

String stringToStars(String s) {
  for (int i = 0; i < s.length(); ++i) {
    s[i] = '*';
  }

  return s;
}
