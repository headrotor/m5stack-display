

/*
  Board: M5Stack-Core-esp32
  ENcoder FACE
  (example code //https://github.com/m5stack/M5-ProductExampleCodes/blob/master/Module/ENCODER/Arduino/faces_encoder/faces_encoder.ino)
*/

// TODO: IP address in status on starup (remove 2 s delay)
// throttle drawing because of crash on rapid redraw?
// visual confirmation of long button press
// "no server" timestamp to draw if powered on with no server send
//battery monitor
// server load?
// draw bargraph for light values
// draw empty bargraph and filled portion


#define SCREENX 360
#define SCREENY 240

#include <Arduino.h>

#include <M5Stack.h>

#include <WiFi.h>
#include <WiFiUdp.h>
//#include <WiFiMulti.h>
//#include <WiFiClientSecure.h>
#include <FastLED.h>


#define Faces_Encoder_I2C_ADDR     0X5E


/* define SPI_LED for Faces Encoder, define WS812_LED for M5Stack */
#define SPI_LED
//#define WS812_LED

// Use original OSC library from CNMAT https://github.com/CNMAT/OSC
// API : https://github.com/CNMAT/OSC/blob/master/API.md
#include <OSCMessage.h>
#include <OSCBundle.h>
#include <OSCData.h>

#include "colors.h"
#include "credentials.h"

// Constants from credentials.h so we don't check them into git!

// SSID and password of wifi connection
//const char* ssid = "SSID";
//const char* pass = "Password";


const IPAddress ip(192, 168, 1, 227);



const IPAddress gateway(192, 168, 1, 1);
const IPAddress subnet(255, 255, 255, 0);


//FACES encoder example
// https://github.com/m5stack/M5-ProductExampleCodes/tree/master/Module/ENCODER/Arduino/faces_encoder
#define FACES
#define NUM_LEDS 12


//for M5stack FIRE, leds are neopixels:
//http://forum.m5stack.com/topic/273/how-use-rgb-led-on-m5-fire/2
// Set pin to 15(GPIO) and number pixels to 10.
//#define FIRE
//#define NUM_LEDS 10
//#define DATA_PIN 15


// if neither FIRE or FACES, no leds
//#define NUM_LEDS 0

CRGB leds[NUM_LEDS];

// A UDP instance to let us send and receive packets over UDP
WiFiUDP Udp;
const IPAddress outIp0(192, 168, 1, 148);     // remote IP (main computer)
const unsigned int outPort0 = 12000;          // remote port (main computer)
const IPAddress outIp1(192, 168, 1, 144);     // remote IP (rpi)
const unsigned int outPort1 = 12000;          // remote port (rpi)
const unsigned int localPort = 10000;        // local port to listen for UDP packets (here's where we listen for the packets)


OSCErrorCode error;
unsigned int ledState = LOW;              // LOW means led is *on*
int volume = 0;
int state = -1;

// blackboard for text to display

#define COLS 64
#define ROWS 10

char disp[ROWS][COLS + 1];


char label[4][COLS + 1]; // store button soft labels here
int msg_lines = 0;


// double-buffered time string
char time_str[2][COLS];
char tbuf = 0;   // will be only 0 or 1 to select 1 of 2 time buffers


// set to 1 if dsiplay text has changed so we don't redraw unless new data
uint8_t redraw = 0;


// fpr LCD

#define GFXFF 1
#define GLCD  0
#define FONT2 2
#define FONT4 4
#define FONT6 6
#define FONT7 7
#define FONT8 8

// set this flag if no udp data recieved, color display
uint16_t stale = 0;


#define USE_SERIAL Serial


// set up encoder, LEDs

int encoder_increment;//positive: clockwise negative: anti-clockwise
int encoder_value = 0;

int old_encoder = 9999;

uint8_t encoder_direction;//0: clockwise 1: anti-clockwise
uint8_t enc_last_button, enc_button;

void check_encoder(void) {
  int temp_encoder_increment = 0;

#ifdef FACES
  encoder_increment = 0;
  Wire.requestFrom(Faces_Encoder_I2C_ADDR, 3);
  if (Wire.available()) {
    temp_encoder_increment = Wire.read();
    enc_button = Wire.read();
  }
  if (temp_encoder_increment > 127) { //anti-clockwise
    encoder_direction = 1;
    encoder_increment = 256 - temp_encoder_increment;
  }
  else {
    encoder_direction = 0;
    encoder_increment = temp_encoder_increment;
  }
#endif
}


void setup_leds() {
#if defined FIRE
  FastLED.addLeds<WS2811, DATA_PIN, GRB>(leds, NUM_LEDS);
#elif defined FACES

#endif
}




void handle_leds(OSCMessage &msg) {
  // deserialize and deal with messages in msgpack format
  char led_str[64];
  char led_str1[64];

  // LED data is strings in the format #RRGGBB where RR is hex value for red, etc.

  //Serial.println("/leds: ");

  int i;
  int LED;
  // LED data is a string of r,g, b, r, g, b, bytes
  int nleds = msg.size();

  for (i = 0; i < nleds; i++) {
    //Serial.print("led message part ");
    //Serial.println(i);

    // copy message lines into display array
    msg.getString(i, led_str1, COLS);
    String lstr = (char*)led_str1;
    //digitalWrite(BUILTIN_LED, ledState);
    //Serial.print(i);
    //Serial.print(" /label: ");
    //Serial.println(lstr);
    lstr.toCharArray(led_str, COLS);

    unsigned long int colorint = strtoul(led_str, 0, 16);

    byte b =  (byte) colorint & 0xFF;
    colorint >>= 8;
    byte g =  (byte) colorint & 0xFF;
    colorint >>= 8;
    byte r =  (byte) colorint & 0xFF;
    set_led(i, r, g, b);



  }
#if defined FIRE
  FastLED.show();
#endif

}

void set_led(int i, int r, int g, int b) {

#if defined FACES
  Wire.beginTransmission(Faces_Encoder_I2C_ADDR);
  Wire.write(i);
  Wire.write(r);
  Wire.write(g);
  Wire.write(b);
  Wire.endTransmission();
#elif defined FIRE

  leds[i].setRGB(r, g, b);

#endif

}

void handle_status(OSCMessage & msg) {
  // deserialize and deal with messages in msgpack format
  char msg_str[COLS];


  //digitalWrite(BUILTIN_LED, ledState);
  Serial.println("/status: ");

  int i;

  msg_lines = msg.size();
  for (i = 0; i < min(msg_lines, ROWS); i++) {
    msg.getString(i, msg_str, COLS);
    String stat = (char*)msg_str;
    // copy message lines into display array
    stat.toCharArray(disp[i], COLS);
    Serial.println(msg_str);
  }
  msg_lines = i;

  redraw = 2;
}

void handle_time(OSCMessage & msg) {
  // deserialize and deal with messages in msgpack format
  char msg_str[COLS];

  //Serial.print("/time: ");
  //Serial.println(stat);

  msg.getString(0, msg_str, COLS);
  String times = (char*)msg_str;
  // copy message lines into display array
  tbuf = 1 - tbuf; // toggle tbuf
  times.toCharArray(time_str[tbuf], COLS);

  redraw = 1;
  stale = 0;

  //USE_SERIAL.println(msg1);
}



void handle_labels(OSCMessage & msg) {
  // deserialize and deal with messages in msgpack format
  char msg_str[COLS];


  byte val;
  int i;

  //Serial.print(" /label: ");
  for (i = 0; i < msg.size(); i++) {
    // copy message lines into display array
    msg.getString(i, msg_str, COLS);
    String lstr = (char*)msg_str;

    //Serial.println(lstr);
    lstr.toCharArray(label[i], COLS);
  }


  redraw = 1;
  //USE_SERIAL.println(msg1);
}

void handle_volume(OSCMessage & msg) {
  // deserialize and deal with messages in msgpack format
  byte val;
  int i;

  volume = msg.getInt(0);
  volume = constrain(volume, 0, 100);

  state = msg.getInt(1);

  //Serial.print("vol=");
  //Serial.println(volume);
  redraw = 1;
}


void clear_blackboard() {
  // set all display strings to zero-length
  for (int i = 0; i < ROWS; i++) {
    disp[i][0] = '\0';
    disp[i][0] = '\0';
  }
}


/********************************************************
   SETUP
 ******************************************************/
void setup() {
  // USE_SERIAL.begin(921600);

  clear_blackboard();

  USE_SERIAL.begin(115200);

  M5.begin();
  setup_leds();

  Wire.begin();
  USE_SERIAL.setDebugOutput(true);

  USE_SERIAL.println();
  M5.Lcd.setFreeFont(&FreeSans9pt7b);                 // Select the font

  for (uint8_t t = 0; t > 0; t--) {
    USE_SERIAL.printf("[SETUP] BOOT WAIT %d...\n", t);
    USE_SERIAL.flush();
    M5.Lcd.printf("[SETUP] BOOT WAIT %d...\n", t);

    delay(250);
  }

  M5.Lcd.print("\nConnecting");

  WiFi.begin((char *)ssid, (char *)pass);
  WiFi.config(ip, gateway, subnet);
  while ( WiFi.status() != WL_CONNECTED ) {
    delay(250);
    Serial.print(".");
    M5.Lcd.print(".");
  }
  M5.Lcd.println("");


  // Print our IP address
  Serial.println("Connected!");
  Serial.print("My IP address: ");
  Serial.println(WiFi.localIP());

  M5.Lcd.print("My IP address: ");
  M5.Lcd.println(WiFi.localIP());
  strncpy(disp[0], "local IP", COLS);
  String ipstr = WiFi.localIP().toString();
  ipstr.toCharArray(disp[1], COLS);

  Serial.println("Starting UDP");
  Udp.begin(localPort);
  Serial.print("Local port: ");
  M5.Lcd.print("Local port: ");
#ifdef ESP32
  Serial.println(localPort);
  M5.Lcd.println(localPort);
  sprintf(disp[2], "port: %i", localPort);

#endif

  msg_lines = 3;
  redraw = 2;

  // display ip in status


  clear_display();
}

#define STATE_STOP 0
#define STATE_PAUSE 1
#define STATE_PLAY 2


void clear_display() {
  M5.Lcd.fillScreen(TFT_BLACK);            // Clear screen
}


void paint_display() {
  int i;

  // draw charging indicator:
	int batt = M5.Power.getBatteryLevel();

  // clear all dots


	if (batt < 100) {
		// draw red dot 
		M5.Lcd.fillCircle(10, SCREENY-20,  5, TFT_RED);    
		if (batt > 25) 
			M5.Lcd.fillCircle(10, SCREENY-40, 5, TFT_YELLOW);    
		else
			M5.Lcd.fillCircle(10, SCREENY-40, 5, TFT_BLACK);
			
		if (batt > 50) 
			M5.Lcd.fillCircle(10, SCREENY-60,  5, TFT_GREEN);    
		else
			M5.Lcd.fillCircle(10, SCREENY-60, 5, TFT_BLACK);			
	}
	else {
			M5.Lcd.fillCircle(10, SCREENY-20, 5, TFT_BLACK);
			M5.Lcd.fillCircle(10, SCREENY-40, 5, TFT_BLACK);
			M5.Lcd.fillCircle(10, SCREENY-60, 5, TFT_BLACK);
	}
  
  /*
  if (M5.Power.isCharging()) {
    //M5.Lcd.fillCircle(0, 0, 320, 10, TFT_BLACK);    
    M5.Lcd.drawRoundRect(0,10, 10, 10, 5, TFT_GREEN);
  } else {
    M5.Lcd.drawRoundRect(0,10, 10, 10, 5, TFT_RED);
  }
*/
  if (redraw == 0)
    return;

    
  M5.Lcd.setTextDatum(MC_DATUM);

  // Set text colour to orange with black background


  if (redraw == 2) {
    M5.Lcd.fillScreen(TFT_BLACK);            // Clear screen
  }

  M5.Lcd.setFreeFont(&FreeSans12pt7b);                 // Select the font


  // draw volume bar
  //drawRoundRect(int16_t x0, int16_t y0, int16_t w,  int16_t h, int16_t radius, uint16_t color);


  M5.Lcd.fillRect(0, 0, 320, 10, TFT_BLACK);
  switch (state) {
    case STATE_STOP:
      M5.Lcd.drawRoundRect(0, 0, (int16_t) int(3.2 * volume), 10, 5, TFT_WHITE);
      break;

    case STATE_PLAY:
      M5.Lcd.fillRoundRect(0, 0, (int16_t) int(3.2 * volume), 10, 5, TFT_WHITE);
      break;

    case STATE_PAUSE:
      M5.Lcd.fillRoundRect(0, 0, (int16_t) int(3.2 * volume), 10, 5, TFT_SLATEBLUE);
      break;

    default:
      M5.Lcd.fillRoundRect(0, 0, (int16_t) int(3.2 * volume), 10, 5, TFT_RED);
      break;

  }

  // draw new strings in white
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
  for (i = 0; i < msg_lines; i++) {
    //M5.Lcd.setTextColor(TFT_BLACK, TFT_BLACK);
    //M5.Lcd.setFreeFont(&FreeSans12pt7b);
    //M5.Lcd.drawString((const char*)disp[1 - dbuf][i], 160, 50 + (26 * i), GFXFF); // Print the string name o

    if (strlen(disp[i]) > 28) {
      M5.Lcd.setFreeFont(&FreeSans9pt7b);
    } else {
      M5.Lcd.setFreeFont(&FreeSans12pt7b);
    }

    M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);
    M5.Lcd.drawString((const char*)disp[i], 160, 50 + (26 * i), GFXFF); // Print the string name o
  }


  M5.Lcd.setFreeFont(&FreeSans12pt7b);
  // draw time after other labels

  // draw old time in black to erase
  M5.Lcd.setTextColor(TFT_BLACK, TFT_BLACK);
  M5.Lcd.drawString((const char*)time_str[1 - tbuf], 160, 60 + (26 * 5), GFXFF); // Print the string name o

  // draw new time in gray
  if (stale) {
    M5.Lcd.setTextColor(TFT_RED, TFT_BLACK);
  }
  else {
    M5.Lcd.setTextColor(TFT_LIGHTGREY, TFT_BLACK);

  }
  M5.Lcd.drawString((const char*)time_str[tbuf], 160, 60 + (26 * 5), GFXFF); // Print the string name o


  // now draw labels

  M5.Lcd.setTextColor(TFT_BLUE, TFT_BLACK);
  for (i = 0; i < msg_lines; i++) {
    M5.Lcd.drawString((const char*)label[i], 60 + (95 * i), 220, GFXFF);
  }

  redraw = 0;

}


void OSC_loop() {
  OSCMessage msg;
  int size = Udp.parsePacket();

  if (size > 0) {
    while (size--) {
      msg.fill(Udp.read());
    }
    if (!msg.hasError()) {
      msg.dispatch("/status", handle_status);
      msg.dispatch("/labels", handle_labels);
      msg.dispatch("/time", handle_time);
      msg.dispatch("/volume", handle_volume);
      if (NUM_LEDS > 0) {
        msg.dispatch("/leds", handle_leds);

      }
    } else {
      error = msg.getError();
      Serial.print("error: ");
      Serial.println(error);
    }
  }
}


// constants for OSC messages
#define BUTA 0x02
#define LONGA 0x03
#define BUTB 0x04
#define LONGB  0x05
#define BUTC 0x08
#define LONGC 0x09
#define INCR 0x10
#define DECR 0x11
#define PUSH 0x12
#define HEART 0x13

char longpress = 0;


void encoder_loop(void) {
  check_encoder();

  if (encoder_increment) {
    /*
        Serial.println("");
        Serial.print("incr = ");
        Serial.println(encoder_increment);
        Serial.print("dir =");
        Serial.println(encoder_direction);
    */
    if (encoder_direction == 0) {
      send_OSC(INCR);
      //Serial.println("INCR");
    }
    if (encoder_direction == 1) {
      send_OSC(DECR);
      //Serial.println("DECR");
    }

  }

  if (enc_button != enc_last_button) {
    //Serial.print("    button_state: ");
    //Serial.println(enc_button);
    enc_last_button = enc_button;

    // value of zero means button pressed, send pause command
    if (enc_button == 0) {
      send_OSC(PUSH);
      Serial.println("PUSH");
    }
  }

}
/****************************************************************************************
   LOOP
*/

void do_timer() {
  static unsigned long last_time = 0;
  unsigned long now = millis();

  if ((now - last_time) > 1000) {
    //Serial.print("charging: ");
    //Serial.println(M5.Power.isCharging());
    
    //Serial.print("battery: ");
    //Serial.println(M5.Power.getBatteryLevel());
    send_OSC(HEART);
    last_time = now;
    if (stale == 1) {
      redraw = 1;
    }
    stale = 1;
  }


}

void loop() {
  OSC_loop();
  M5.update();

#ifdef FACES
  encoder_loop();
#endif

  paint_display();
  do_timer();


  if (M5.BtnA.pressedFor(500)) {
    longpress |= BUTA;
  }

  if (M5.BtnB.pressedFor(500)) {
    longpress |= BUTB;
  }

  if (M5.BtnC.pressedFor(500)) {
    longpress |= BUTC;
  }

  if  (M5.BtnA.wasReleased()) {

    if (longpress & BUTA) {
      send_OSC(LONGA);
      Serial.println("sent longpress A");
    }    else {
      send_OSC(BUTA);
      Serial.println("sent shortpress A");
    }
    // clear longpress bit
    longpress = longpress & !BUTA;

  }


  if  (M5.BtnB.wasReleased()) {

    if (longpress & BUTB) {
      send_OSC(LONGB);
      Serial.println("sent longpress B");
    }    else {
      send_OSC(BUTB);
      Serial.println("sent shortpress B");
    }
    longpress = longpress & !BUTB;

  }


  if  (M5.BtnC.wasReleased()) {

    if (longpress & BUTC) {
      send_OSC(LONGC);
      Serial.println("sent longpress C");
    }    else {
      send_OSC(BUTC);
      Serial.println("sent shortpress C");
    }
    longpress = longpress & !BUTC;

  }


  // if you want to use Releasefor("was released for"), use .wasReleasefor(int time) below
  /*

    if (M5.BtnA.wasReleased()) {
      send_OSC(0);
    } else if (M5.BtnB.wasReleased()) {
      send_OSC(1);
    } else if (M5.BtnC.wasReleased()) {
      send_OSC(2);
    } else if (M5.BtnA.wasReleasefor(500)) {
      send_OSC(3);
    }
  */

}

void send_OSC(int but) {
  OSCMessage msg("/buttonQ                  ");

  switch (but) {
    case LONGA:
      msg.setAddress("/buttonA");
      msg.add((float)0.5);
      break;

    case BUTA:
      msg.setAddress("/buttonA");
      msg.add((float)0.0);
      break;


    case LONGB:
      msg.setAddress("/buttonB");
      msg.add((float)0.5);
      break;

    case BUTB:
      msg.setAddress("/buttonB");
      msg.add((float)0.0);
      break;


    case BUTC:
      msg.setAddress("/buttonC");
      msg.add((float)0.0);
      break;

    case LONGC:
      msg.setAddress("/buttonC");
      msg.add((float)0.5);
      break;

    case INCR:
      msg.setAddress("/encoder");
      msg.add((float) 1.);
      break;

    case DECR:
      msg.setAddress("/encoder");
      msg.add((float) - 1.);
      break;

    case PUSH:
      msg.setAddress("/encoder");
      msg.add((float) 0.);
      break;

    case HEART:
      msg.setAddress("/heartbeat");
      break;

    default:
      return;

  }

  //Serial.println("UDP SENT");
  Udp.beginPacket(outIp0, outPort0);
  msg.send(Udp);
  Udp.endPacket();

  Udp.beginPacket(outIp1, outPort1);
  msg.send(Udp);
  Udp.endPacket();
  msg.empty();

  //clear_display();

}
