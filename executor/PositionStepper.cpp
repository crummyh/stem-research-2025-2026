#include "PositionStepper.h"
#include <Arduino.h>

PositionStepper::PositionStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir) {
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
    this->movingToTarget = false;
    this->currentPosition = 0;
    this->targetPosition = 0;
    this->lastStepTime = 0;
    this->pulseHigh = false;
    this->pulseStartTime = 0;

    // Default speed: 2 RPM
    setSpeed(2.0);
}

void PositionStepper::setSpeed(float rpm) {
    // Convert RPM to steps per second
    this->speed = (rpm * this->stepsPerRev) / 60.0;
    updateStepInterval();
}

void PositionStepper::updateStepInterval() {
    // Calculate microseconds between steps
    if (this->speed > 0) {
        this->stepInterval = (unsigned long)(1000000.0 / this->speed);
    } else {
        this->stepInterval = 1000000; // Very slow default
    }
}

void PositionStepper::start() {
    this->stopped = false;
    // digitalWrite(this->enaPin, LOW);
    this->lastStepTime = micros();
}

void PositionStepper::stop() {
    this->stopped = true;
    this->movingToTarget = false;
    // digitalWrite(this->enaPin, HIGH); // Disable motor
    digitalWrite(this->pulPin, LOW); // Ensure pulse is low
    this->pulseHigh = false;
}

bool PositionStepper::startMoveToPosition(long pos) {
    if (this->stopped) {
        return false; // Can't move while stopped
    }

    // if (this->movingToTarget) {
    //     return false; // Already moving to a position
    // }

    this->targetPosition = pos;

    long stepsToGo = targetPosition - currentPosition;

    // if (stepsToGo == 0) {
    //     return false; // Already at target
    // }

    // Set direction
    bool moveForward = stepsToGo > 0;

    // Apply direction inversion if needed
    bool dirPinState = (moveForward != inverseDir);

    digitalWrite(this->dirPin, dirPinState ? HIGH : LOW);
    delayMicroseconds(5); // Direction setup time for driver

    this->movingToTarget = true;
    this->lastStepTime = micros();
    this->pulseHigh = false;

    return true;
}

void PositionStepper::updatePosition() {
    if (stopped || !movingToTarget) {
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
        long stepsToGo = targetPosition - currentPosition;

        if (stepsToGo == 0) {
            // Reached target
            movingToTarget = false;
            return;
        }

        // Generate step pulse
        digitalWrite(pulPin, HIGH);
        pulseHigh = true;
        pulseStartTime = currentTime;
        lastStepTime = currentTime;

        // Update position based on direction
        if (stepsToGo > 0) {
            currentPosition++;
        } else {
            currentPosition--;
        }
    }
}

int PositionStepper::rotationsToSteps(float rotations) {
    return (int)(rotations * this->stepsPerRev);
}
