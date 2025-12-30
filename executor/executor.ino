#include "PacketProtocol.h"
#include "PositionStepper.h"

#define tempMotorPul 5
#define tempMotorDir 6
#define tempMotorEna 7

// const float PI = 3.14159;
const int STEPS_PER_REV = 400;

PositionStepper testSteeper(tempMotorPul, tempMotorDir, tempMotorEna, STEPS_PER_REV, false);

PacketProtocol protocol;

uint8_t mode;


float radsToRevs(float rads) {
    return rads * 2 * PI;
}

// Packet handler callback
void onPacketReceived(PacketType type, const uint8_t* payload, uint8_t length) {
    switch (type) {
        case PING:
            if (!protocol.sendPong()) {
                digitalWrite(LED_BUILTIN, HIGH);
            }
            break;

        case CMD_START:
            testSteeper.start();
            protocol.sendAck();
            break;

        case CMD_STOP:
            testSteeper.stop();
            protocol.sendAck();
            break;

        case CMD_SET_MODE: {
            if (length >= 1) {
                mode = payload[0];
                // Set operating mode
                protocol.sendAck();
            }
            break;
        }

        case CMD_SET_PARAM: {
            uint8_t paramId;
            float value;
            if (PacketParser::parseSetParamFloat(payload, length, paramId, value)) {
                // Handle parameter setting
                protocol.sendAck();
            }
            break;
        }

        case CMD_SET_TENDONS: {
            int32_t m1, m2, m3;
            if (PacketParser::parseTendons(payload, length, m1, m2, m3)) {
                // Control 3 motors
                // moveStepper1(m1);
                // moveStepper2(m2);
                // moveStepper3(m3);
                protocol.sendAck();
            }
            break;
        }

        case CMD_SET_SPOOL: {
            int32_t steps;
            if (PacketParser::parseSpool(payload, length, steps)) {
                // Control single motor
                // moveStepper4(steps);
                protocol.sendAck();
            }
            break;
        }

        case CMD_READ_SENSOR: {
            uint8_t sensorId;
            if (PacketParser::parseReadSensor(payload, length, sensorId)) {
                // Read sensor and send data
                // float value = readSensor(sensorId);
                // protocol.sendSensorData(sensorId, value);
            }
            break;
        }

        case NACK: {
            break;
        }

        default:
            protocol.sendNack(type);  // Unknown command
            break;
    }
}

void setup() {
    Serial.begin(115200);
    protocol.begin(&Serial, onPacketReceived);

    testSteeper.start(); // VERY BAD
    testSteeper.startMoveToPosition(400);
}

void loop() {
    // Process incoming packets
    protocol.update();

    // Periodically send status updates
    static unsigned long lastStatus = 0;
    if (millis() - lastStatus > 1000) {
        protocol.sendStatusUpdate(mode, 0x0, millis());
        lastStatus = millis();
    }

    testSteeper.updatePosition();
}
