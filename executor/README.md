# Executor

This code is ran on a non-genuine Arduino Nano with an ATmega328P.

## Notes

The FQBN is `arduino:avr:nano`

The code can be compiled and uploaded with
```bash
arduino-cli compile --fqbn arduino:avr:nano executor
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano executor
```
