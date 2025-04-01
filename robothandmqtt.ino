#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <WiFi.h>
#include <PubSubClient.h>  // Include the MQTT client library

// MQTT Setup
const char* mqtt_server = "192.168.113.250";  // IP of Raspberry Pi (Mosquitto Broker)
const int mqtt_port = 1883;
const char* mqtt_topic = "test/topic";   // Topic to subscribe to

WiFiClient espClient;  // Client to connect to the MQTT broker
PubSubClient client(espClient);  // MQTT client instance

#define MIN_PULSE_WIDTH       650
#define MAX_PULSE_WIDTH       2350
#define DEFAULT_PULSE_WIDTH   1500
#define FREQUENCY             50

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

void setup() {
    Serial.begin(115200);
    Serial.println("ESP32-CAM Robot Hand - Ready for MQTT Commands");

    // Setup WiFi (replace with your Wi-Fi credentials)
    WiFi.begin("Farhan's Galaxy A54 5G FEA9", "incorrect");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("WiFi Connected!");

    // Setup MQTT client
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(mqttCallback);

    Wire.begin(14, 15); // SDA = 14, SCL = 15
    pwm.begin();
    pwm.setPWMFreq(FREQUENCY);
}

void loop() {
    if (!client.connected()) {
        reconnectMQTT();
    }
    client.loop();  // Listen for incoming messages
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String message = "";
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    message.trim();  // Remove unwanted spaces or newline characters

    Serial.print("Received MQTT message: ");
    Serial.println(message);
    
    processCommand(message);  // Process the received message
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

void reconnectMQTT() {
    // Loop until we're reconnected
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        if (client.connect("ESP32Client")) {
            Serial.println("connected");
            client.subscribe(mqtt_topic);  // Subscribe to the MQTT topic
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            delay(5000);  // Wait for 5 seconds before trying again
        }
    }
}
