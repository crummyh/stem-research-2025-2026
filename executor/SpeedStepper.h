#ifndef PositionStepper_h
#define PositionStepper_h

#include "PositionStepper.h"
#include <Arduino.h>

class SpeedStepper {
    public:
    SpeedStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir);

    // Set speed in RPM
    void setSpeed(float speed);

    void stop();

    void start();

    void updatePosition();

    int getCurrentPosition();

    float getCurrentRotations();

    int rotationsToSteps(float rotations);

    private:

    int currentPosition;

    int stepsPerRev;

    // Speed in *steps per second*
    int speed;

    bool inverseDir;

    bool stopped;

    int pulPin;
    int dirPin;
    int enaPin;

    unsigned long lastLoopTime;
    float posOverflow;
};

#endif
