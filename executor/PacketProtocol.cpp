#include <Arduino.h>
#include <inttypes.h>
#include "PacketProtocol.h"

PacketProtocol::PacketProtocol()
    : serial(nullptr), handler(nullptr), rxBufferIndex(0),
      packetsSent(0), packetsReceived(0), packetsInvalid(0) {
}

void PacketProtocol::begin(Stream* serialPort, PacketHandler packetHandler) {
    serial = serialPort;
    handler = packetHandler;
    rxBufferIndex = 0;
}

void PacketProtocol::setHandler(PacketHandler packetHandler) {
    handler = packetHandler;
}

uint8_t PacketProtocol::calculateChecksum(const uint8_t* data, uint8_t length) {
    uint8_t checksum = 0;
    for (uint8_t i = 0; i < length; i++) {
        checksum ^= data[i];
    }
    return checksum;
}

bool PacketProtocol::validatePacket(const uint8_t* packet, uint8_t length) {
    if (length < MIN_PACKET_SIZE) return false;
    if (packet[0] != PACKET_START_BYTE) return false;

    uint8_t payloadLength = packet[2];
    uint8_t expectedLength = MIN_PACKET_SIZE + payloadLength;

    if (length != expectedLength) return false;

    // Verify checksum (XOR of TYPE + LENGTH + PAYLOAD)
    uint8_t checksum = calculateChecksum(&packet[1], length - 2);
    return checksum == packet[length - 1];
}

void PacketProtocol::update() {
    if (!serial) return;

    // Read available data into buffer
    while (serial->available() && rxBufferIndex < sizeof(rxBuffer)) {
        rxBuffer[rxBufferIndex++] = serial->read();
    }

    // Process one complete packet if available
    if (rxBufferIndex >= MIN_PACKET_SIZE) {
        processBuffer();
    }
}

void PacketProtocol::processBuffer() {
    // Find start byte
    uint16_t startIdx = 0;
    for (; startIdx < rxBufferIndex; startIdx++) {
        if (rxBuffer[startIdx] == PACKET_START_BYTE) {
            break;
        }
    }

    // Remove data before start byte
    if (startIdx > 0) {
        memmove(rxBuffer, rxBuffer + startIdx, rxBufferIndex - startIdx);
        rxBufferIndex -= startIdx;
    }

    // Check if we have enough data for a complete packet
    if (rxBufferIndex < MIN_PACKET_SIZE) return;

    uint8_t payloadLength = rxBuffer[2];
    uint8_t packetLength = MIN_PACKET_SIZE + payloadLength;

    if (rxBufferIndex < packetLength) return;

    // Validate packet
    bool isValid = validatePacket(rxBuffer, packetLength);

    // Remove packet from buffer
    uint8_t tempPacket[MIN_PACKET_SIZE + MAX_PAYLOAD_SIZE];
    memcpy(tempPacket, rxBuffer, packetLength);
    memmove(rxBuffer, rxBuffer + packetLength, rxBufferIndex - packetLength);
    rxBufferIndex -= packetLength;

    // Now handle the packet (safe to send responses)
    if (isValid) {
        handlePacket(tempPacket, packetLength);
        packetsReceived++;
    } else {
        packetsInvalid++;
    }
}

void PacketProtocol::handlePacket(const uint8_t* packet, uint8_t length) {
    if (!handler) return;

    PacketType type = (PacketType)packet[1];
    uint8_t payloadLength = packet[2];
    const uint8_t* payload = (payloadLength > 0) ? &packet[3] : nullptr;

    handler(type, payload, payloadLength);
}

bool PacketProtocol::sendPacket(PacketType type, const uint8_t* payload, uint8_t length) {
    if (!serial) return false;
    if (length > MAX_PAYLOAD_SIZE) return false;

    // Build packet
    uint8_t packet[MIN_PACKET_SIZE + MAX_PAYLOAD_SIZE];
    packet[0] = PACKET_START_BYTE;
    packet[1] = (uint8_t)type;
    packet[2] = length;

    // Copy payload
    if (length > 0 && payload != nullptr) {
        memcpy(&packet[3], payload, length);
    }

    // Calculate and add checksum
    uint8_t packetLength = MIN_PACKET_SIZE + length;
    packet[packetLength - 1] = calculateChecksum(&packet[1], packetLength - 2);

    // Send packet
    size_t written = serial->write(packet, packetLength);

    if (written == packetLength) {
        packetsSent++;
        return true;
    }
    return false;
}

bool PacketProtocol::sendPing() {
    return sendPacket(PING);
}

bool PacketProtocol::sendPong() {
    return sendPacket(PONG);
}

bool PacketProtocol::sendAck(uint8_t sequenceNum) {
    return sendPacket(ACK, &sequenceNum, 1);
}

bool PacketProtocol::sendNack(uint8_t errorCode) {
    return sendPacket(NACK, &errorCode, 1);
}

bool PacketProtocol::sendStatusUpdate(uint8_t mode, uint8_t state, uint32_t uptime) {
    uint8_t payload[6];
    payload[0] = mode;
    payload[1] = state;
    memcpy(&payload[2], &uptime, 4);
    return sendPacket(STATUS_UPDATE, payload, 6);
}

bool PacketProtocol::sendSensorData(uint8_t sensorId, float value) {
    uint8_t payload[5];
    payload[0] = sensorId;
    memcpy(&payload[1], &value, 4);
    return sendPacket(SENSOR_DATA, payload, 5);
}

bool PacketProtocol::sendErrorReport(uint8_t errorCode, const uint8_t* data, uint8_t dataLen) {
    uint8_t payload[MAX_PAYLOAD_SIZE];
    payload[0] = errorCode;

    uint8_t totalLen = 1;
    if (data != nullptr && dataLen > 0) {
        uint8_t copyLen = min(dataLen, (uint8_t)(MAX_PAYLOAD_SIZE - 1));
        memcpy(&payload[1], data, copyLen);
        totalLen += copyLen;
    }

    return sendPacket(ERROR_REPORT, payload, totalLen);
}

void PacketProtocol::clearBuffer() {
    rxBufferIndex = 0;
}

// PacketParser implementation
bool PacketParser::parseSetParam(const uint8_t* payload, uint8_t length,
                                uint8_t& paramId, int32_t& value) {
    if (length < 5) return false;
    paramId = payload[0];
    memcpy(&value, &payload[1], 4);
    return true;
}

bool PacketParser::parseSetParamFloat(const uint8_t* payload, uint8_t length,
                                      uint8_t& paramId, float& value) {
    if (length < 5) return false;
    paramId = payload[0];
    memcpy(&value, &payload[1], 4);
    return true;
}

bool PacketParser::parseTendons(const uint8_t* payload, uint8_t length,
                                   int32_t& motor1, int32_t& motor2, int32_t& motor3) {
    if (length < 12) return false;
    memcpy(&motor1, &payload[0], 4);
    memcpy(&motor2, &payload[4], 4);
    memcpy(&motor3, &payload[8], 4);
    return true;
}

bool PacketParser::parseSpool(const uint8_t* payload, uint8_t length,
                                    int32_t& motorSteps) {
    if (length < 4) return false;
    memcpy(&motorSteps, payload, 4);
    return true;
}

bool PacketParser::parseReadSensor(const uint8_t* payload, uint8_t length,
                                   uint8_t& sensorId) {
    if (length < 1) return false;
    sensorId = payload[0];
    return true;
}
