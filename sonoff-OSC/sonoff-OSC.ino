

#include <ArduinoOSC.h>

// from https://github.com/hideakitai/ArduinoOSC
// install via library manager


#include <Debouncer.h>
//https://github.com/hideakitai/Debouncer
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




#include "credentials.h"

// Constants from credentials.h so we don't check them into git!
//const char* ssid = "SSID";
//const char* pwd = "Password";

#define PUSHBUTTON 0
#define RELAY_PIN 12
#define LED_PIN 13


//todo: switch colors etc. from touchOSC


#define ADDR 5

const IPAddress ip(192, 168, 1, 220 + ADDR);
const IPAddress gateway(192, 168, 1, 1);
const IPAddress subnet(255, 255, 255, 0);

// pidp
//const char* host = "192.168.1.144";

// scrut
const char* host = "192.168.1.149";
const int recv_port = 10000;
const int send_port = 12000;

const int bind_port = 54345;
const int publish_port = 54445;

int relay_stat = LOW;


// values for timers
#define DEBOUNCE_DELAY 10
unsigned long timer_start = 0;
// milliseconds to time out and toggle relay
// zero value indicates timer is not running
unsigned long timer_delay_ms = 0;
Debouncer button(PUSHBUTTON, DEBOUNCE_DELAY);

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

  //OscWiFi.publish(host, publish_port, "/publish/value", relay_stat)
  //->setFrameRate(10.f);

  OscWiFi.subscribe(recv_port, "/switch",
                    [](const OscMessage & m)
  {
    Serial.print(m.remoteIP()); Serial.print(" ");
    Serial.print(m.remotePort()); Serial.print(" ");
    Serial.print(m.size()); Serial.print(" ");
    Serial.print(m.address()); Serial.print(" ");
    Serial.println(m.arg<int>(0)); Serial.print(" ");
    if (m.size() > 1) {
      Serial.print(m.arg<float>(1)); Serial.println(" ");
      timer_start = millis();
      timer_delay_ms = (unsigned long)(1000L * m.arg<float>(1));
      Serial.print("Timer set for ms ");
      Serial.println(timer_delay_ms);
    }


    if ((m.arg<int>(0)) > 0) {
      set_relay(1);
    }
    else {
      set_relay(0);
    }
  }
                   );


  OscWiFi.subscribe(recv_port, "/toggle",
                    [](const OscMessage & m)
  {
    Serial.print(m.remoteIP()); Serial.print(" ");
    Serial.print(m.remotePort()); Serial.print(" ");
    Serial.println(m.address()); Serial.print(" ");
    toggle();

  }

                   );

  OscWiFi.subscribe(recv_port, "/status",
                    [](const OscMessage & m)
  {
    Serial.print(m.remoteIP()); Serial.print(" ");
    Serial.print(m.remotePort()); Serial.print(" ");
    Serial.println(m.address()); Serial.print(" ");
    post_status();
  }

                   );


  pinMode(PUSHBUTTON, INPUT_PULLUP);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  Serial.println("START");

  pinMode(LED_PIN, OUTPUT); // inverted, low to light
  digitalWrite(LED_PIN, HIGH);


  // blink address on LED on startup
  for (int i = 0; i < ADDR; i++) {
    digitalWrite(LED_PIN, LOW);
    delay(300);
    digitalWrite(LED_PIN, HIGH);
    delay(100);
  }
  digitalWrite(LED_PIN, LOW);

}

void loop() {

  //OscWiFi.update();
  OscWiFi.update(); // to receive osc

  button.update();
  if (button.edge()) {
    if (button.falling())        {
      Serial.print("fall : ");
      toggle();

    }
  }

  if (timer_delay_ms) {
    if ((millis() - timer_start) > timer_delay_ms) {
      Serial.println("Timer up!");
      toggle();
      timer_delay_ms = 0;
    }
  }
}

void toggle(void) {
  set_relay(1 - relay_stat);
}

void set_relay(byte value) {
  relay_stat = value;
  digitalWrite(LED_PIN, relay_stat);
  digitalWrite(RELAY_PIN, relay_stat);
  Serial.print("Set relay:");
  Serial.println(relay_stat);
  post_status();

}


void post_status(void) {
  OscWiFi.send(host, send_port, "/status", relay_stat);

  //OscWiFi.post();
}
