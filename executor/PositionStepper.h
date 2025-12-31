#ifndef POSITION_STEPPER_H
#define POSITION_STEPPER_H

#include <Arduino.h>

class PositionStepper {
private:
    int pulPin;
    int dirPin;
    int enaPin;
    int stepsPerRev;
    bool inverseDir;

    float speed; // Steps per second
    bool stopped;

    long currentPosition; // Current position in steps
    long targetPosition;  // Target position in steps
    bool movingToTarget;

    unsigned long lastStepTime; // Micros of last step pulse
    unsigned long stepInterval;  // Microseconds between steps
    bool pulseHigh; // Track pulse state for non-blocking pulse generation
    unsigned long pulseStartTime; // When current pulse went high

    static const unsigned long PULSE_WIDTH_US = 3; // Minimum pulse width

    void updateStepInterval();

public:
    PositionStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir = false);

    void setSpeed(float rpm); // Set speed in RPM
    void start();
    void stop();
    bool isStopped() { return stopped; }

    bool startMoveToPosition(long pos); // Returns true if move started
    bool isMoving() { return movingToTarget; }
    long getCurrentPosition() { return currentPosition; }
    long getTargetPosition() { return targetPosition; }
    long getRemainingSteps() { return abs(targetPosition - currentPosition); }

    void updatePosition(); // Call this in loop() as often as possible

    void setCurrentPosition(long pos) { currentPosition = pos; } // For homing/zeroing
    int rotationsToSteps(float rotations);
};

#endif
