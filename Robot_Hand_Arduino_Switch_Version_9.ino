#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "BluetoothSerial.h"
BluetoothSerial SerialBT;

#define MIN_PULSE_WIDTH       650
#define MAX_PULSE_WIDTH       2350
#define DEFAULT_PULSE_WIDTH   1500
#define FREQUENCY             50

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
#define BLUETOOTH "ESP32BT"
#if defined(BLUETOOTH)
  #include "esp32dumbdisplay.h"
  DumbDisplay dumbdisplay(new DDBluetoothSerialIO(BLUETOOTH));
#endif
void setup() {
    Serial.begin(115200);
    Serial.println("ESP32-CAM Robot Hand - Ready for Commands");
    SerialBT.begin(115200);
    Wire.begin(14, 15); // SDA = 14, SCL = 15
    pwm.begin();
    pwm.setPWMFreq(FREQUENCY);
}

void loop() {
    if (SerialBT.available()) {
        String inByte = SerialBT.readString();
        inByte.trim(); // Remove unwanted spaces or newline characters
        
        Serial.print("Raw Received: '");
        Serial.print(inByte);
        Serial.println("'");
        
        // Print each character in HEX to detect hidden characters
        Serial.print("HEX Values: ");
        for (int i = 0; i < inByte.length(); i++) {
            Serial.print((int)inByte[i], HEX);
            Serial.print(" ");
        }
        Serial.println();

        if (inByte.length() > 0) {
            processCommand(inByte);
        }
    }
}


void processCommand(String command) {
    for (int i = 0; i < command.length(); i++) {
        char c = command.charAt(i);
        
        if (c == '\n' || c == '\r') continue; // Ignore newlines
        
        Serial.print("Processing: ");
        Serial.println(c);
        
        switch (c) {
            case '-': resetServos(); break;
            case 'a': moveServos(0, 180, 180, 180, 180); break;
            case 'b': moveServos(180, 0, 0, 0, 0); break;
            case 'c': moveServos(120, 140, 130, 95, 165); break;
            case 'd': moveServos(145, 0, 145, 145, 165); break;
            case 'e': moveServos(180, 180, 180, 180, 180); break;
            case 'f': moveServos(180, 180, 0, 0, 0); break;
            case 'i': moveServos(180, 180, 180, 180, 0); break;
            case 'k': moveServos(90, 0, 0, 180, 180); break;
            case 'l': moveServos(0, 0, 180, 180, 180); break;
            case 'm': moveServos(180, 160, 160, 160, 180); break;
            case 'n': moveServos(180, 160, 160, 160, 160); break;
            case 'o': moveServos(180, 180, 180, 180, 180); break;
            case 's': moveServos(180, 180, 180, 180, 180); break;
            case 't': moveServos(140, 160, 180, 180, 180); break;
            case 'u': moveServos(120, 0, 0, 180, 180); break;
            case 'v': moveServos(120, 0, 0, 180, 180); break;
            case 'w': moveServos(120, 0, 0, 0, 180); break;
            case 'x': moveServos(180, 90, 160, 160, 160); break;
            case 'y': moveServos(0, 180, 180, 180, 0); break;
            case '0': moveServos(180, 180, 180, 180, 180); break;
            case '1': moveServos(180, 0, 180, 180, 180); break;
            case '2': moveServos(180, 0, 0, 180, 180); break;
            case '3': moveServos(0, 0, 0, 180, 180); break;
            case '4': moveServos(180, 0, 0, 0, 0); break;
            case '5': resetServos(); break;
            case '6': moveServos(180, 0, 0, 60, 180); break;
            case '7': moveServos(180, 0, 0, 180, 0); break;
            case '8': moveServos(180, 0, 180, 0, 0); break;
            case '9': moveServos(180, 180, 0, 0, 0); break;
            default: 
                Serial.print("Unknown command: ");
                Serial.println(c);
                break;
        }
        delay(1000);
        resetServos();
    }
}


void moveServos(int th, int in, int mid, int ring, int pinky) {
    pwm.setPWM(0, 0, pulseWidth(th));
    pwm.setPWM(1, 0, pulseWidth(in));
    pwm.setPWM(2, 0, pulseWidth(mid));
    pwm.setPWM(3, 0, pulseWidth(ring));
    pwm.setPWM(4, 0, pulseWidth(pinky));
}

void resetServos() {
    moveServos(0, 0, 0, 0, 0);
}

int pulseWidth(int angle) {
    int pulse_wide = map(angle, 0, 180, MIN_PULSE_WIDTH, MAX_PULSE_WIDTH);
    int analog_value = int(float(pulse_wide) / 1000000 * FREQUENCY * 4096);
    return analog_value;
}
