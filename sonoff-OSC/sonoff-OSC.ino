

#include <ArduinoOSC.h>

// from https://github.com/hideakitai/ArduinoOSC
// install via library manager


// board install instructions: https://github.com/esp8266/Arduino

// Select "Generic ESP8285" in board manager


// Sonoff instructiopms
// https://medium.com/@jeffreyroshan/flashing-a-custom-firmware-to-sonoff-wifi-switch-with-arduino-ide-402e5a2f77b

// Hold button down and cycle power to enter flash mode


/*
  Upload Using: Serial
  CPU Frequency: 80MHz
  Flash Size: 1M (64K SPIFFS)
  Debug Port: Disabled
  Debug Level: None
  Reset Method: ck
  Upload Speed: 115200
*/


// watchdog problems use https://github.com/me-no-dev/EspExceptionDecoder#installation

#include "credentials.h"


// Constants from credentials.h so we don't check them into git!
//const char* ssid = "SSID";
//const char* pwd = "Password";


#define RELAY_PIN 12
#define LED_PIN 13

// milliseconds to time out and turn off relay
// zero value indicates timer is not running
unsigned long relay_timeout = 0;

//todo: switch colors etc. from touchOSC


const IPAddress ip(192, 168, 1, 220);
const IPAddress gateway(192, 168, 1, 1);
const IPAddress subnet(255, 255, 255, 0);

// pidp
//const char* host = "192.168.1.144";

// scrut
const char* host = "192.168.1.149";
const int recv_port = 10000;
const int send_port = 12000;




void setup() {
  Serial.begin(115200);


  // WiFi stuff
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pwd);
  WiFi.config(ip, gateway, subnet);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.print("\n\nWiFi connected, IP = "); Serial.println(WiFi.localIP());

  OscWiFi.subscribe(recv_port, "/switch",
                    [](const OscMessage & m)
  {
    Serial.print(m.remoteIP()); Serial.print(" ");
    Serial.print(m.remotePort()); Serial.print(" ");
    Serial.print(m.size()); Serial.print(" ");
    Serial.print(m.address()); Serial.print(" ");
    Serial.print(m.arg<int>(0)); Serial.print(" ");
    //Serial.print(m.arg<float>(1)); Serial.print(" ");
    //Serial.print(m.arg<String>(2)); Serial.println();

    if ((m.arg<int>(0)) > 0) {
      digitalWrite(LED_PIN, HIGH);
      digitalWrite(RELAY_PIN, HIGH);

    }
    else {
      digitalWrite(LED_PIN, LOW);
      digitalWrite(RELAY_PIN, LOW);

    }
  }
                   );



  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  Serial.println("START");

  pinMode(LED_PIN, OUTPUT);

}

void loop() {

  OscWiFi.update();
  //  digitalWrite(LED_PIN, HIGH);
  //  digitalWrite(RELAY_PIN, HIGH);
  //  delay(500);
  //
  //  digitalWrite(LED_PIN, LOW);
  //  digitalWrite(RELAY_PIN, LOW);
  //  delay(500);
  //
  //  Serial.println("LED");

}
