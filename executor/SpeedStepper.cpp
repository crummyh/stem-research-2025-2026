#include "SpeedStepper.h"
#include <Arduino.h>

SpeedStepper::SpeedStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir) {
    this->pulPin = pulPin;
    this->dirPin = dirPin;
    this->enaPin = enaPin;

    pinMode(this->pulPin, OUTPUT);
    pinMode(this->dirPin, OUTPUT);
    pinMode(this->enaPin, OUTPUT);

    this->stepsPerRev = stepsPerRev;
    this->inverseDir = inverseDir;
    this->stopped = true;

    this->setSpeed(0);

    this->posOverflow = 0;
    this->currentPosition = 0;
}

void SpeedStepper::setSpeed(float speed) {
    this->speed = this->stepsPerRev * speed / 60;
}

void SpeedStepper::stop() {
    this->stopped = true;
}

void SpeedStepper::start() {
    this->stopped = false;
    this->lastLoopTime = micros(); // Make sure time is not counted while stopped
}

void SpeedStepper::updatePosition() {
    unsigned int deltaTime = micros() - this->lastLoopTime;

    if (this->stopped) {
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

    for (int i = 0; i < neededSteps; i++) {
        digitalWrite(this->pulPin, HIGH);
        delayMicroseconds(3);
        digitalWrite(this->pulPin, LOW);
        this->currentPosition += this->inverseDir ? -1 : 1;
        delayMicroseconds(3);
    }

    this->lastLoopTime = micros();
}

int SpeedStepper::rotationsToSteps(float rotations) {
    return (int) (rotations * this->stepsPerRev);
}
