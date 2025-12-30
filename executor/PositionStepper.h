#ifndef PositionStepper_h
#define PositionStepper_h

#include <Arduino.h>

class PositionStepper {
    public:
    PositionStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir);

    // Set speed in RPM
    void setSpeed(float speed);

    // Start moving towards pos (steps)
    bool startMoveToPosition(int pos);

    void stop();

    void start();

    // Continue moving towards the set point every loop
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

    // Absolute distance between our goal and current position
    int absPosDiff;

    unsigned long lastLoopTime;
    float posOverflow;
};

#endif
