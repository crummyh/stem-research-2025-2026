#ifndef CONTINUOUS_STEPPER_H
#define CONTINUOUS_STEPPER_H

class ContinuousStepper {
private:
    int pulPin;
    int dirPin;
    int enaPin;
    int stepsPerRev;
    bool inverseDir;

    float speed; // steps per second (can be negative for reverse)
    bool stopped;

    long currentPosition; // Current position in steps (tracks total movement)

    unsigned long lastStepTime; // Micros of last step pulse
    unsigned long stepInterval;  // Microseconds between steps
    bool pulseHigh; // Track pulse state for non-blocking pulse generation
    unsigned long pulseStartTime; // When current pulse went high

    static const unsigned long PULSE_WIDTH_US = 3; // Minimum pulse width

    void updateStepInterval();
    void updateDirection();

public:
    ContinuousStepper(int pulPin, int dirPin, int enaPin, int stepsPerRev, bool inverseDir = false);
    #ifndef PositionStepper_h
    #define PositionStepper_h

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

    void setSpeed(float rpm); // Set speed in RPM (positive = forward, negative = reverse, 0 = stop motion)
    float getSpeed(); // Get current speed in RPM
    void start(); // Enable motor
    void stop(); // Disable motor
    bool isStopped() { return stopped; }

    void run(); // Call this in loop() as often as possible

    long getCurrentPosition() { return currentPosition; } // Total steps moved
    void setCurrentPosition(long pos) { currentPosition = pos; } // For homing/zeroing
    int rotationsToSteps(float rotations);
};

#endif
