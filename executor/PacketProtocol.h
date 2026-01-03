#ifndef PACKET_PROTOCOL_H
#define PACKET_PROTOCOL_H

#include <inttypes.h>
#include <Arduino.h>

// Packet type definitions
enum PacketType: uint8_t {
    // Bidirectional packets
    PING = 0x01,  // Ping (Do you hear me?)
    PONG = 0x02,  // Pong (I hear you!)
    ACK = 0x03,  // Acknowledge (Understood)
    NACK = 0x04,  // Negative Acknowledge (I don't understand)

    // Space left here

    // Supervisor -> Executor (Commands)
    CMD_SET_MODE = 0x10,  // Set operating mode
    CMD_SET_PARAM = 0x11,  // Set a parameter (Float or int-32)
    CMD_START = 0x12,  // Start Operation
    CMD_STOP = 0x13,  // Stop Operation
    CMD_RESET = 0x14,  // Reset Command
    CMD_READ_SENSOR = 0x15,  // Request sensor data
    CMD_SET_TENDONS = 0x16,  // Set tendon steering
    CMD_SET_SPOOL = 0x17,  // Set spool position

    // Space left here

    // Executor -> Supervisor (Data/Status)
    STATUS_UPDATE = 0x20,  // Status update
    SENSOR_DATA = 0x21,  // Sensor data response
    ERROR_REPORT = 0x22,  // Error report
    DEBUG_MESSAGE = 0x23,  // Debug message
};

// Packet structure constants
const uint8_t PACKET_START_BYTE = 0xAA;
const uint8_t MAX_PAYLOAD_SIZE = 255;
const uint8_t MIN_PACKET_SIZE = 4;  // START + TYPE + LENGTH + CHECKSUM

// Callback function type for packet handlers
typedef void (*PacketHandler)(PacketType type, const uint8_t* payload, uint8_t length);

class PacketProtocol {
public:
    PacketProtocol();

    // Initialize with serial interface and optional handler
    void begin(Stream* serial, PacketHandler handler = nullptr);

    // Set packet handler callback
    void setHandler(PacketHandler handler);

    // Process incoming serial data (call in loop())
    void update();

    // Send a packet
    bool sendPacket(PacketType type, const uint8_t* payload = nullptr, uint8_t length = 0);

    // Convenience methods for common packets
    bool sendPing();
    bool sendPong();
    bool sendAck(uint8_t sequenceNum = 0);
    bool sendNack(uint8_t errorCode = 0);
    bool sendStatusUpdate(uint8_t mode, uint8_t state, uint32_t uptime);
    bool sendSensorData(uint8_t sensorId, float value);
    bool sendErrorReport(uint8_t errorCode, const uint8_t* data = nullptr, uint8_t dataLen = 0);

    // Statistics
    uint32_t getPacketsSent() const { return packetsSent; }
    uint32_t getPacketsReceived() const { return packetsReceived; }
    uint32_t getPacketsInvalid() const { return packetsInvalid; }

    // Buffer management
    void clearBuffer();

private:
    Stream* serial;
    PacketHandler handler;

    // Receive buffer
    uint8_t rxBuffer[MIN_PACKET_SIZE + MAX_PAYLOAD_SIZE];
    uint16_t rxBufferIndex;

    // Statistics
    uint32_t packetsSent;
    uint32_t packetsReceived;
    uint32_t packetsInvalid;

    // Internal methods
    uint8_t calculateChecksum(const uint8_t* data, uint8_t length);
    bool validatePacket(const uint8_t* packet, uint8_t length);
    void processBuffer();
    void handlePacket(const uint8_t* packet, uint8_t length);
};

// Helper class for parsing common payloads
class PacketParser {
public:
    // Parse CMD_SET_PARAM payload
    static bool parseSetParamId(const uint8_t* payloat, uint8_t length,
                                uint8_t& paramID);
    static bool parseSetParam(const uint8_t* payload, uint8_t length,
                             uint8_t& paramId, int32_t& value);
    static bool parseSetParamFloat(const uint8_t* payload, uint8_t length,
                                   uint8_t& paramId, float& value);

    // Parse motor control packets
    static bool parseTendons(const uint8_t* payload, uint8_t length,
                               float& motor1, float& motor2, float& motor3);
    static bool parseSpool(const uint8_t* payload, uint8_t length,
                                float& motorSteps);

    // Parse sensor read request
    static bool parseReadSensor(const uint8_t* payload, uint8_t length,
                               uint8_t& sensorId);
};

#endif
