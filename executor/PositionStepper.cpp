#include "PositionStepper.h"
#include <Arduino.h>

PositionStepper::PositionStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir) {
    this->pulPin = pulPin;
    this->dirPin = dirPin;
    this->enaPin = enaPin;

    pinMode(this->pulPin, OUTPUT);
    pinMode(this->dirPin, OUTPUT);
    pinMode(this->enaPin, OUTPUT);

    this->stepsPerRev = stepsPerRev;
    this->inverseDir = inverseDir;
    this->stopped = true;

    // this->speed = this->stepsPerRev / 30; // 2 rpm
    this->setSpeed(this->stepsPerRev / 30.0);

    this->posOverflow = 0;
    this->currentPosition = 0;
}

void PositionStepper::setSpeed(float speed) {
    this->speed = this->stepsPerRev * speed / 60;
}

bool PositionStepper::startMoveToPosition(int pos) {
    if (this->stopped) {
        return false;
    }

    int relativePosition = currentPosition - pos;

    bool isClockwise;
    if (relativePosition > 0) {
        if (!inverseDir) {
            isClockwise = false;
        } else {
            isClockwise = true;
        }
    } else if (relativePosition < 0) {
        if (!inverseDir) {
            isClockwise = true;
        } else {
            isClockwise = false;
        }
    } else {
        // Relative position is 0
        return;
    }

    if (isClockwise) {
        digitalWrite(this->dirPin, HIGH);
        delayMicroseconds(5);
    } else {
        digitalWrite(this->dirPin, LOW);
        delayMicroseconds(5);
    }

    this->absPosDiff = abs(relativePosition);

    return true;
}

void PositionStepper::stop() {
    this->stopped = true;
}

void PositionStepper::start() {
    this->stopped = false;
    this->lastLoopTime = micros(); // Make sure time is not counted while stopped
}

void PositionStepper::updatePosition() {
    unsigned int deltaTime = micros() - this->lastLoopTime;

    if (this->stopped) {
        return;
    }

    if (this->absPosDiff == 0) {
        return;
    }

    float neededStepsF = ((float) this->speed / 1000000) * deltaTime;
    int neededSteps = neededStepsF;
    this->posOverflow += neededStepsF - neededSteps;

    if (posOverflow > 1) {
        int intOverflowValue = (int) posOverflow;
        this->posOverflow -= intOverflowValue;
        neededSteps += intOverflowValue;
    }

    for (int i = 0; i < neededSteps && this->absPosDiff > 0; i++) {
        digitalWrite(this->pulPin, HIGH);
        delayMicroseconds(3);
        digitalWrite(this->pulPin, LOW);
        this->absPosDiff -= 1;
        delayMicroseconds(3);
    }

    this->lastLoopTime = micros();
}

int PositionStepper::rotationsToSteps(float rotations) {
    return (int) (rotations * this->stepsPerRev);
}
