#include "PacketProtocol.h"

PacketProtocol protocol;

uint8_t mode;

// Packet handler callback
void onPacketReceived(PacketType type, const uint8_t* payload, uint8_t length) {
    switch (type) {
        case PING:
            protocol.sendPong();
            break;

        case CMD_START:
            // Start your motors/process
            protocol.sendAck();
            break;

        case CMD_STOP:
            // Stop motors
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
                float value = readSensor(sensorId);
                protocol.sendSensorData(sensorId, value);
            }
            break;
        }

        default:
            protocol.sendNack(0xFF);  // Unknown command
            break;
    }
}

void setup() {
    Serial.begin(115200);
    protocol.begin(&Serial, onPacketReceived);
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

    // Your loop code here
}

float readSensor(uint8_t id) {
    // Placeholder - read actual sensor
    return analogRead(A0) * 0.1;
}
