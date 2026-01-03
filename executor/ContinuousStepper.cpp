#include "ContinuousStepper.h"
#include <Arduino.h>

ContinuousStepper::ContinuousStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir) {
    this->pulPin = pulPin;
    this->dirPin = dirPin;
    this->enaPin = enaPin;
    this->stepsPerRev = stepsPerRev;
    this->inverseDir = inverseDir;

    pinMode(this->pulPin, OUTPUT);
    pinMode(this->dirPin, OUTPUT);
    pinMode(this->enaPin, OUTPUT);

    digitalWrite(this->pulPin, LOW);
    // digitalWrite(this->enaPin, HIGH);

    this->stopped = true;
    this->currentPosition = 0;
    this->lastStepTime = 0;
    this->pulseHigh = false;
    this->pulseStartTime = 0;
    this->speed = 0;
    this->stepInterval = 1000000;
}

void ContinuousStepper::setSpeed(float rpm) {
    // Convert RPM to steps per second (keep sign for direction)
    this->speed = (rpm * this->stepsPerRev) / 60.0;
    updateStepInterval();
    updateDirection();
}

float ContinuousStepper::getSpeed() {
    // Convert steps per second back to RPM
    return (this->speed * 60.0) / this->stepsPerRev;
}

void ContinuousStepper::updateStepInterval() {
    // Calculate microseconds between steps (use absolute value of speed)
    float absSpeed = abs(this->speed);
    if (absSpeed > 0) {
        this->stepInterval = (unsigned long)(1000000.0 / absSpeed);
    } else {
        this->stepInterval = 1000000; // Very slow default when stopped
    }
}

void ContinuousStepper::updateDirection() {
    if (this->speed == 0) {
        return; // No direction change needed when not moving
    }

    // Determine direction: positive speed = forward, negative = reverse
    bool moveForward = (this->speed > 0);

    // Apply direction inversion if needed
    bool dirPinState = (moveForward != inverseDir); // XOR logic

    digitalWrite(this->dirPin, dirPinState ? HIGH : LOW);
    delayMicroseconds(5); // Direction setup time for driver
}

void ContinuousStepper::start() {
    this->stopped = false;
    // digitalWrite(this->enaPin, LOW);
    this->lastStepTime = micros();
    updateDirection();
}

void ContinuousStepper::stop() {
    this->stopped = true;
    // digitalWrite(this->enaPin, HIGH);
    digitalWrite(this->pulPin, LOW); // Ensure pulse is low
    this->pulseHigh = false;
}

void ContinuousStepper::run() {
    if (stopped || speed == 0) {
        return;
    }

    unsigned long currentTime = micros();

    // Handle pulse completion (bring pulse low after PULSE_WIDTH_US)
    if (pulseHigh && (currentTime - pulseStartTime >= PULSE_WIDTH_US)) {
        digitalWrite(pulPin, LOW);
        pulseHigh = false;
    }

    // Check if it's time for the next step
    if (!pulseHigh && (currentTime - lastStepTime >= stepInterval)) {
        // Generate step pulse
        digitalWrite(pulPin, HIGH);
        pulseHigh = true;
        pulseStartTime = currentTime;
        lastStepTime = currentTime;

        // Update position based on direction (speed sign)
        if (speed > 0) {
            currentPosition++;
        } else {
            currentPosition--;
        }
    }
}

int ContinuousStepper::rotationsToSteps(float rotations) {
    return (int)(rotations * this->stepsPerRev);
}
