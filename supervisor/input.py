from typing import Callable, final
import pygame
import sys
import threading
import time


@final
class Buttons:
    A = 0
    B = 1
    X = 2
    Y = 3


class Controller:
    def __init__(self, joystick_id: int = 0, poll_rate: float = 0.01):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No game controller detected.")
            sys.exit()

        self.joystick = pygame.joystick.Joystick(joystick_id)
        self.joystick.init()

        self.poll_rate = poll_rate

        self.button_down_handlers = {}
        self.button_up_handlers = {}

        self.prev_buttons = [0] * self.joystick.get_numbuttons()

        self.running = False

    def on_button_down(self, button_id: int, callback: Callable[..., None]):
        self.button_down_handlers[button_id] = callback

    def on_button_up(self, button_id, callback):
        self.button_up_handlers[button_id] = callback

    def _poll(self):
        while self.running:
            pygame.event.pump()
            buttons = [
                self.joystick.get_button(i)
                for i in range(self.joystick.get_numbuttons())
            ]

            for i, state in enumerate(buttons):
                if state and not self.prev_buttons[i]:
                    # Button pressed
                    if i in self.button_down_handlers:
                        self.button_down_handlers[i]()
                elif not state and self.prev_buttons[i]:
                    # Button released
                    if i in self.button_up_handlers:
                        self.button_up_handlers[i]()

            self.prev_buttons = buttons
            time.sleep(self.poll_rate)

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._poll, daemon=True).start()

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.running = False
        pygame.quit()
