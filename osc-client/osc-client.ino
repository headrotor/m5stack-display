/*


*/

#include <Arduino.h>

#include <WiFi.h>
#include <WiFiUdp.h>
//#include <WiFiMulti.h>
#include <WiFiClientSecure.h>
#include <M5Stack.h>

// Use original OSC library from CNMAT https://github.com/CNMAT/OSC
// API : https://github.com/CNMAT/OSC/blob/master/API.md
#include <OSCMessage.h>
#include <OSCBundle.h>
#include <OSCData.h>

#include "colors.h"
#include "credentials.h"

// Constants from credentials.h so we don't check them into git!

// //SSID and password of wifi connection
//const char* ssid = "SSID";
//const char* password = "Password";


// A UDP instance to let us send and receive packets over UDP
WiFiUDP Udp;
const IPAddress outIp(192, 168, 1, 148);     // remote IP (not needed for receive)
const unsigned int outPort = 12000;          // remote port (not needed for receive)
const unsigned int localPort = 10000;        // local port to listen for UDP packets (here's where we send the packets)


OSCErrorCode error;
unsigned int ledState = LOW;              // LOW means led is *on*




// blackboard for text to display

#define COLS 32
#define ROWS 10

char disp[ROWS][COLS + 1];
char label[4][COLS + 1]; // store button soft labels here
int msg_lines = 0;
char time_str[COLS];

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


#define USE_SERIAL Serial





void handle_status(OSCMessage &msg) {
  // deserialize and deal with messages in msgpack format
  char msg_str[COLS];

  //digitalWrite(BUILTIN_LED, ledState);
  Serial.print("/status: ");

  int i;
  
  msg_lines = msg.size();
  for (i = 0; i < msg_lines; i++) {
    msg.getString(i, msg_str, COLS);
    String stat = (char*)msg_str;
    // copy message lines into display array
    stat.toCharArray(disp[i], COLS);
  }


  redraw = 1;
  //USE_SERIAL.println(msg1);
}

void handle_time(OSCMessage &msg) {
  // deserialize and deal with messages in msgpack format
  char msg_str[COLS];

  Serial.print("/time: ");
  //Serial.println(stat);

  msg.getString(0, msg_str, COLS);
  String times = (char*)msg_str;
  // copy message lines into display array
  times.toCharArray(time_str, COLS);

  redraw = 1;
  //USE_SERIAL.println(msg1);
}


void handle_labels(OSCMessage &msg) {
  // deserialize and deal with messages in msgpack format
  char msg_str[COLS];


  byte val;
  int i;


  for (i = 0; i < msg.size(); i++) {
    // copy message lines into display array
    msg.getString(i, msg_str, COLS);
    String lstr = (char*)msg_str;
    //digitalWrite(BUILTIN_LED, ledState);
    Serial.print(i);
    Serial.print(" /label: ");
    Serial.println(lstr);
    lstr.toCharArray(label[i], COLS);
  }


  redraw = 1;
  //USE_SERIAL.println(msg1);
}



void clear_blackboard() {
  // set all display strings to zero-length
  for (int i = 0; i < ROWS; i++) {
    disp[i][0] = '\0';
  }
}



void setup() {
  // USE_SERIAL.begin(921600);

  clear_blackboard();

  USE_SERIAL.begin(115200);

  M5.begin();

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
  while ( WiFi.status() != WL_CONNECTED ) {
    delay(250);
    Serial.print(".");
    M5.Lcd.print(".");
  }


  // Print our IP address
  Serial.println("Connected!");
  Serial.print("My IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Starting UDP");
  Udp.begin(localPort);
  Serial.print("Local port: ");
#ifdef ESP32
  Serial.println(localPort);
#else
  Serial.println(Udp.localPort());
#endif

  //delay(1000);



}


void paint_display() {
  int i;
  if (redraw == 0)
    return;
  M5.Lcd.setTextDatum(MC_DATUM);

  // Set text colour to orange with black background
  M5.Lcd.setTextColor(TFT_WHITE, TFT_BLACK);

  M5.Lcd.fillScreen(TFT_BLACK);            // Clear screen
  M5.Lcd.setFreeFont(&FreeSans12pt7b);                 // Select the font
  for (i = 0; i < msg_lines; i++) {
    M5.Lcd.drawString((const char*)disp[i], 160, 50 + (26 * i), GFXFF); // Print the string name o
  }

  // draw time after other labels
  M5.Lcd.setTextColor(TFT_GRAY, TFT_BLACK);
  M5.Lcd.drawString((const char*)time_str, 160, 60 + (26 * i), GFXFF); // Print the string name o


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
    } else {
      error = msg.getError();
      Serial.print("error: ");
      Serial.println(error);
    }
  }
}

void loop() {
  OSC_loop();
  M5.update();


  paint_display();

  // if you want to use Releasefor("was released for"), use .wasReleasefor(int time) below
  if (M5.BtnA.wasReleased()) {
    send_OSC(0);
  } else if (M5.BtnB.wasReleased()) {
    send_OSC(1);
  } else if (M5.BtnC.wasReleased()) {
    send_OSC(2);
  } else if (M5.BtnA.wasReleasefor(500)) {
    send_OSC(3);
  }

}

void send_OSC(int but) {
  OSCMessage msg("/filter");
  msg.add(but);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp);
  Udp.endPacket();
  msg.empty();

}
