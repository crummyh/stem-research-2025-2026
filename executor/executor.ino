#include "PacketProtocol.h"
#include "PositionStepper.h"
#include "ContinuousStepper.h"

#define MAX_PARAMS 2

// Enable pin is not used right now
#define tendon1MotorPul 5
#define tendon1MotorDir 4
// #define tendon1MotorEna 4

#define tendon2MotorPul 3
#define tendon2MotorDir 2
// #define tendon2MotorEna 1

#define tendon3MotorPul 12
#define tendon3MotorDir 11
// #define tendon3MotorEna 10

#define spoolMotorPul 10
#define spoolMotorDir 9
// #define spoolMotorEna 7

const int TENDON_STEPS_PER_REV = 400;
const int SPOOL_STEPS_PER_REV = 47 * 400; // 47:1 and 400 steps per rev

// Params
enum ParamType { PARAM_FLOAT, PARAM_INT32 };

struct Parameter {
  void* ptr;
  ParamType type;
};

Parameter params[MAX_PARAMS];

int32_t param_tendon_speed = 0;

void initParams() {
    params[0] = {&param_tendon_speed, PARAM_INT32};
}

PositionStepper tendon1Motor(tendon1MotorPul, tendon1MotorDir, 13, TENDON_STEPS_PER_REV);
PositionStepper tendon2Motor(tendon2MotorPul, tendon2MotorDir, 13, TENDON_STEPS_PER_REV);
PositionStepper tendon3Motor(tendon3MotorPul, tendon3MotorDir, 13, TENDON_STEPS_PER_REV);

ContinuousStepper spoolMotor(spoolMotorPul, spoolMotorDir, 13, SPOOL_STEPS_PER_REV);

PacketProtocol protocol;

uint8_t mode;

float radsToRevs(float rads) {
    return rads / (2.0 * PI);
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
            tendon1Motor.start();
            tendon2Motor.start();
            tendon3Motor.start();
            spoolMotor.start();
            protocol.sendAck();
            break;

        case CMD_STOP:
            tendon1Motor.stop();
            tendon2Motor.stop();
            tendon3Motor.stop();
            spoolMotor.stop();
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
            if (paramId >= MAX_PARAMS || params[paramId].ptr == nullptr) {
                protocol.sendNack();
                return;
            };

            if (PacketParser::parseSetParamId(payload, length, paramId)) {
                if (params[paramId].type == PARAM_FLOAT) {
                    float value;
                    if (PacketParser::parseSetParamFloat(payload, length, paramId, value)) {
                        *(float*)params[paramId].ptr = value;
                    } else {
                        protocol.sendNack();
                    }
                } else {
                    int32_t value;
                    if (PacketParser::parseSetParam(payload, length, paramId, value)) {
                        *(int32_t*)params[paramId].ptr = value;

                        // This is bad but I really don't want to find a better way right now
                        if (paramId == 0) {
                            tendon1Motor.setSpeed(value);
                            tendon2Motor.setSpeed(value);
                            tendon3Motor.setSpeed(value);
                        }
                    } else {
                        protocol.sendNack();
                    }
                }
            } else {
                protocol.sendNack();
            }
        }

        case CMD_SET_TENDONS: {
            float m1, m2, m3;
            if (PacketParser::parseTendons(payload, length, m1, m2, m3)) {
                if (!(
                    tendon1Motor.startMoveToPosition(tendon1Motor.rotationsToSteps(radsToRevs(m1))) &&
                    tendon2Motor.startMoveToPosition(tendon2Motor.rotationsToSteps(radsToRevs(m2))) &&
                    tendon3Motor.startMoveToPosition(tendon3Motor.rotationsToSteps(radsToRevs(m3)))
                )) {
                    protocol.sendNack(0x00);
                    break;
                }
                protocol.sendAck();
            }
            break;
        }

        case CMD_SET_SPOOL: {
            float speed; // rpm
            if (PacketParser::parseSpool(payload, length, speed)) {
                spoolMotor.setSpeed(speed);
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
    initParams();
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

    tendon1Motor.updatePosition();
    tendon2Motor.updatePosition();
    tendon3Motor.updatePosition();
    spoolMotor.run();
}
