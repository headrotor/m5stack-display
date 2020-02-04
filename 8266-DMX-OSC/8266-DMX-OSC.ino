#include <ArduinoOSC.h>

// from https://github.com/hideakitai/ArduinoOSC
// install via library manager


// board is Wemos D1 mini  (8266)
// schmatic https://wiki.wemos.cc/_media/products:d1:sch_d1_mini_v3.0.0.pdf
// board install instructions: https://github.com/esp8266/Arduino

// select Wemos D1 R1 in board manager


// also see https://github.com/mtongnz/espDMX/issues/7


// watchdog problems use https://github.com/me-no-dev/EspExceptionDecoder#installation

// crashy! Problems with interrupts?
// #include <espDMX.h>
// https://github.com/mtongnz/espDMX

// local version of https://github.com/Rickgg/ESP-Dmx/
#include "ESPDMX.h"


#include <FastLED.h>

#include "credentials.h"


// Constants from credentials.h so we don't check them into git!
//const char* ssid = "SSID";
//const char* pwd = "Password";



// PINOUT:

// D4 -- DMX TX to level converter (actual GPIO2)
// D7 -- output for relay switch 

#define RELAY_PIN D7

// milliseconds to time out and turn off relay
// zero value indicates timer is not running
unsigned long relay_timeout = 0;

//todo: switch colors etc. from touchOSC


const IPAddress ip(192, 168, 1, 243);
const IPAddress gateway(192, 168, 1, 1);
const IPAddress subnet(255, 255, 255, 0);

// for ArduinoOSC
OscWiFi osc;
//const char* host = "192.168.1.123";
const char* host = "192.168.1.100";
const int recv_port = 10000;
const int send_port = 12000;



// roughly 100 hz
#define FADE_MS (4)


#define NUM_LEDS 4

// current colors (for fade) 0.0 to 1.0
float fade_curr[NUM_LEDS];

// fade increment (can be negative)
float fade_incr[NUM_LEDS] = {0., 0., 0., 0.};

// For error-diffusion dithering; propogate error to next fade interval
float fade_error[NUM_LEDS] = {0., 0., 0., 0.};


// For error-diffusion dithering; this is clean value without dither
float fade_clean[NUM_LEDS];

// Fade to this value 0.0 to 1.0
float fade_target[NUM_LEDS] = {0., 1., 0., 0.};



//byte dmx_chans[NUM_LEDS];



// default: use error-diffusion dithering
byte dither_flag = 1;

// default: use FastLED gamma correction
byte gamma_flag = 1;


// fade time in seconds
float fade_time = 1.0;

unsigned long last_ms = 0;


DMXESPSerial dmx;

void setup() {


  //dmxB.begin(12);
  dmx.init(NUM_LEDS + 1);


  // Start Serial port
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


  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);



  osc.begin(recv_port);
  init_osc_callbacks();

  last_ms =  millis();

}

void loop() {

  if ((millis() - last_ms) > FADE_MS) {
    do_fade();
    last_ms = millis();
    dmx.update();
  }

  if (relay_timeout > 0) {

    //delay(1);
    if (millis() > relay_timeout) {
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("RELAY TIMEOUT OFF");
      relay_timeout = 0;
    }

  }
  //      Serial.println("OFF");
  //delay(1);
  osc.parse(); // should be called
  digitalWrite(LED_BUILTIN, LOW);
  ESP.wdtFeed();
}


void start_fade() {
  // new color targets so calculate increments and start fade
  int i;
  // how many FADE_MS periods do we have to execute this fade?
  float fade_count = fade_time * 1000. / float(FADE_MS);
  //Serial.print("fade count ");
  //Serial.println(fade_count);
  for (i = 0; i < NUM_LEDS; i++) {
    fade_error[i] = 0.;
    fade_incr[i] = float(fade_target[i] - fade_clean[i]) / fade_count;
    //Serial.print(" fade incr:");
    //Serial.println(fade_incr[i]);

  }

}

void do_fade() {
  // call this at FADE_MS milliseconds to implemement fading


  int needfade = 0;
  for (int i = 0; i < NUM_LEDS; i++) {
    if (fade_incr[i] != 0.) {
      ++needfade;
    }
  }

  if (needfade == 0) {
    return;
  }

  //Serial.println(" fading--");

  for (int i = 0; i < NUM_LEDS; i++) {


    if (fade_incr[i] > 0) { // if we're incrementing and we're at target
      if (fade_clean[i] >= fade_target[i]) {
        fade_incr[i] = 0.;
        fade_error[i] = 0.;
      }
    }
    else if (fade_incr[i] < 0) {
      // we're decrementing and we're at target
      if (fade_clean[i] <= fade_target[i]) {
        fade_incr[i] = 0.;
        fade_error[i] = 0.;
      }
    }

    //Serial.print(" fade curr:");
    //Serial.println(fade_curr[i]);



    fade_clean[i] += fade_incr[i];
    fade_clean[i] = constrain(fade_clean[i], 0., 1.);


    if (dither_flag)
      fade_curr[i] = fade_clean[i] + (fade_error[i] / 255.);
    else
      fade_curr[i] = fade_clean[i];

    /*
        if (i == 0) {
          Serial.print("fe: ");
          Serial.println(fade_error[i]);
          Serial.print("byte: ");
          Serial.println(round(fade_curr[i] * 255.));
        }
    */

  }
  write_dmx();

  for (int i = 0; i < NUM_LEDS; i++) {
    fade_error[i] = ((fade_curr[i] * 255.) - round(fade_curr[i] * 255.));
  }


}


void write_dmx() {

  // use gamma dimming from FastLED library
  for (int i = 0; i < NUM_LEDS; i++) {
    if (gamma_flag) {
      //Serial.println((byte) round(fade_curr[i] * 255.));

      dmx.write(i + 1, dim8_raw((byte) round(fade_curr[i] * 255.)));    // channel 0 holds start bytes

      //dmx_chans[i] = dim8_raw((byte) round(fade_curr[i] * 255.));
    }
    else {
      dmx.write(i + 1,(byte) round(fade_curr[i] * 255.));
    }
  }

  //dmxB.setChans(dmx_chans, NUM_LEDS, 1);
}


void init_osc_callbacks() {


  osc.subscribe("/setgamma", [](OscMessage & m)
  {
    int i;
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.print("setgamma: ");
    gamma_flag =  (m.arg<int>(0) > 0);
    Serial.println(gamma_flag);

  });

  osc.subscribe("/setdither", [](OscMessage & m)
  {
    int i;
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.print("setdither: ");
    dither_flag =  (m.arg<int>(0) > 0);
    Serial.println(dither_flag);
  });


  osc.subscribe("/switch", [](OscMessage & m)
  {
    int i;
    digitalWrite(LED_BUILTIN, HIGH);
    Serial.print("/switch, length = ");
    Serial.print(m.size());
    Serial.println("");
    int value =  (m.arg<int>(0) > 0);
    if (value > 0) {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("ON");
      if (m.size() > 1) {
        // we got a timeout argument in ms
        relay_timeout = millis() +  m.arg<int>(1);
        // this could overflow but hard to test for because undefined
      }


    } else {
      digitalWrite(RELAY_PIN, LOW);
      relay_timeout = 0;
      Serial.println("OFF");
    }


  });


  osc.subscribe("/hexfade", [](OscMessage & m)
  {
    int i;
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.print("hexcolor: ");
    Serial.println(m.arg<String>(0));
    String s = m.arg<String>(0);

    fade_time = (float) m.arg<float>(1);
    Serial.print("fade_time: ");
    Serial.println(fade_time);
    //const char *cs = s.c_str();
    unsigned long int colorint = strtoul(s.c_str(), 0, 16);

    byte a  = (byte) colorint & 0xFF;
    colorint >>= 8;
    byte b  = (byte) colorint & 0xFF;
    colorint >>= 8;
    byte g  = (byte) colorint & 0xFF;
    colorint >>= 8;
    byte r  = (byte) colorint & 0xFF;

    fade_target[0] = float(r) / 255.;
    fade_target[1] = float(g) / 255.;
    fade_target[2] = float(b) / 255.;
    fade_target[3] = float(a) / 255.;

    if (fade_time <= (FADE_MS) / 1000.) {
      for (i = 0; i < NUM_LEDS; i++) {
        fade_curr[i] = fade_target[i];
        fade_incr[i] = 0;
        write_dmx();
        dmx.update();
      }
    }
    else {
      start_fade();
    }
  });

  /*

    // for touchOSC control
    osc.subscribe("/1/fader1", [](OscMessage & m)
    {
      digitalWrite(LED_BUILTIN, HIGH);

      Serial.print("fader1 : ");
      Serial.println(m.arg<float>(0));
      float f1 = m.arg<float>(0);
      byte val = (byte) int(f1 * 255);
      dmx_chans[1] = val;
      Serial.println(val);
      dmxB.setChans(dmx_chans, NUM_LEDS, 1);
    });

    osc.subscribe("/1/fader1", [](OscMessage & m)
    {
      digitalWrite(LED_BUILTIN, HIGH);

      Serial.print("fader1 : ");
      Serial.println(m.arg<float>(0));
      float f1 = m.arg<float>(0);
      byte val = (byte) int(f1 * 255);
      dmx_chans[0] = val;
      Serial.println(val);
      dmxB.setChans(dmx_chans, NUM_LEDS, 1);
    });

    osc.subscribe("/1/fader2", [](OscMessage & m)
    {
      digitalWrite(LED_BUILTIN, HIGH);

      Serial.print("fader2 : ");
      Serial.println(m.arg<float>(0));
      float f1 = m.arg<float>(0);
      byte val = (byte) int(f1 * 255);
      dmx_chans[1] = val;
      Serial.println(val);
      dmxB.setChans(dmx_chans, NUM_LEDS, 1);
    });

    osc.subscribe("/1/fader3", [](OscMessage & m)
    {
      digitalWrite(LED_BUILTIN, HIGH);

      Serial.print("fader3 : ");
      Serial.println(m.arg<float>(0));
      float f1 = m.arg<float>(0);
      byte val = (byte) int(f1 * 255);
      dmx_chans[2] = val;
      Serial.println(val);
      dmxB.setChans(dmx_chans, NUM_LEDS, 1);
    });

    osc.subscribe("/1/fader4", [](OscMessage & m)
    {
      digitalWrite(LED_BUILTIN, HIGH);

      Serial.print("fader4 : ");
      Serial.println(m.arg<float>(0));
      float f1 = m.arg<float>(0);
      byte val = (byte) int(f1 * 255);
      dmx_chans[3] = val;
      Serial.println(val);
      dmxB.setChans(dmx_chans, NUM_LEDS, 1);
    });

  */

}
