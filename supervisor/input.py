import sys
from time import sleep
from typing import Callable, final

import pygame
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


class ControllerThread(QThread):
    """Thread that polls the game controller and emits Qt signals."""

    # Signals for button events
    button_pressed = pyqtSignal(int)  # button_id
    button_released = pyqtSignal(int)  # button_id

    # Signals for analog stick data
    axis_motion = pyqtSignal(int, float)  # axis_id, value

    # Signal for hat (D-pad) data
    hat_motion = pyqtSignal(int, tuple)  # hat_id, (x, y)

    def __init__(self, joystick_id: int = 0, poll_rate: float = 0.01):
        super().__init__()
        self.joystick_id = joystick_id
        self.poll_rate = poll_rate
        self.running = False
        self.joystick = None
        self.prev_buttons = []
        self.prev_axes = []
        self.prev_hats = []

    def run(self):
        """Main thread loop - initializes pygame and polls controller."""
        pygame.init()
        pygame.joystick.init()

        while pygame.joystick.get_count() == 0:
            return

        self.joystick = pygame.joystick.Joystick(self.joystick_id)
        self.joystick.init()

        # Initialize previous states
        self.prev_buttons = [0] * self.joystick.get_numbuttons()
        self.prev_axes = [0.0] * self.joystick.get_numaxes()
        self.prev_hats = [(0, 0)] * self.joystick.get_numhats()

        self.running = True

        while self.running:
            pygame.event.pump()

            # Check buttons
            for i in range(self.joystick.get_numbuttons()):
                state = self.joystick.get_button(i)
                if state and not self.prev_buttons[i]:
                    self.button_pressed.emit(i)
                elif not state and self.prev_buttons[i]:
                    self.button_released.emit(i)
                self.prev_buttons[i] = state

            # Check axes (joysticks/triggers)
            for i in range(self.joystick.get_numaxes()):
                value = self.joystick.get_axis(i)
                # Only emit if changed significantly (reduce noise)
                if abs(value - self.prev_axes[i]) > 0.01:
                    self.axis_motion.emit(i, value)
                    self.prev_axes[i] = value

            # Check hats (D-pad)
            for i in range(self.joystick.get_numhats()):
                hat = self.joystick.get_hat(i)
                if hat != self.prev_hats[i]:
                    self.hat_motion.emit(i, hat)
                    self.prev_hats[i] = hat

            self.msleep(int(self.poll_rate * 1000))

        pygame.quit()

    def stop(self):
        """Stop the polling thread."""
        self.running = False


@final
class Buttons:
    """Button ID constants"""

    A = 0
    B = 1
    X = 2
    Y = 3
    LB = 4
    RB = 5
    BACK = 6
    START = 7
    L_STICK = 8
    R_STICK = 9


@final
class Axes:
    """Axis ID constants"""

    LEFT_X = 0
    LEFT_Y = 1
    RIGHT_X = 3
    RIGHT_Y = 4
    LEFT_TRIGGER = 2
    RIGHT_TRIGGER = 5
