import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from input import Axes, Buttons, ControllerThread


class VideoStream(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vine Robot Supervisor")

        self.main_layout = QHBoxLayout()
        self.side_layout = QVBoxLayout()

        self.status_label = QLabel("Controller Status: Initializing...")
        self.button_label = QLabel("Last Button: None")
        self.left_stick_label = QLabel("Left Stick: (0.00, 0.00)")
        self.right_stick_label = QLabel("Right Stick: (0.00, 0.00)")
        self.trigger_label = QLabel("Triggers: L=0.00, R=0.00")

        self.side_layout.addWidget(self.status_label)
        self.side_layout.addWidget(self.button_label)
        self.side_layout.addWidget(self.left_stick_label)
        self.side_layout.addWidget(self.right_stick_label)
        self.side_layout.addWidget(self.trigger_label)

        self.main_layout.addWidget(VideoStream("green"))
        self.main_layout.addLayout(self.side_layout)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0

        self.controller_thread = ControllerThread(poll_rate=0.01)

        self.controller_thread.button_pressed.connect(self.on_button_pressed)
        self.controller_thread.button_released.connect(self.on_button_released)
        self.controller_thread.axis_motion.connect(self.on_axis_motion)

        self.controller_thread.start()
        self.status_label.setText("Controller Status: Connected")

    def on_button_pressed(self, button_id: int):
        """Handle button press events."""
        button_names = {
            Buttons.A: "A",
            Buttons.B: "B",
            Buttons.X: "X",
            Buttons.Y: "Y",
            Buttons.LB: "LB",
            Buttons.RB: "RB",
            Buttons.BACK: "Back",
            Buttons.START: "Start",
        }
        name = button_names.get(button_id, f"Button {button_id}")
        self.button_label.setText(f"Last Button: {name} (Pressed)")

    def on_button_released(self, button_id: int):
        """Handle button release events."""
        button_names = {
            Buttons.A: "A",
            Buttons.B: "B",
            Buttons.X: "X",
            Buttons.Y: "Y",
            Buttons.LB: "LB",
            Buttons.RB: "RB",
            Buttons.BACK: "Back",
            Buttons.START: "Start",
        }
        name = button_names.get(button_id, f"Button {button_id}")
        self.button_label.setText(f"Last Button: {name} (Released)")

    def on_axis_motion(self, axis_id: int, value: float):
        """Handle analog stick and trigger motion."""

        if axis_id == Axes.LEFT_X:
            self.left_x = value
            self.left_stick_label.setText(
                f"Left Stick: ({self.left_x:.2f}, {self.left_y:.2f})"
            )
        elif axis_id == Axes.LEFT_Y:
            self.left_y = value
            self.left_stick_label.setText(
                f"Left Stick: ({self.left_x:.2f}, {self.left_y:.2f})"
            )
        elif axis_id == Axes.RIGHT_X:
            self.right_x = value
            self.right_stick_label.setText(
                f"Right Stick: ({self.right_x:.2f}, {self.right_y:.2f})"
            )
        elif axis_id == Axes.RIGHT_Y:
            self.right_y = value
            self.right_stick_label.setText(
                f"Right Stick: ({self.right_x:.2f}, {self.right_y:.2f})"
            )
        elif axis_id == Axes.LEFT_TRIGGER:
            self.left_trigger = value
            self.trigger_label.setText(
                f"Triggers: L={self.left_trigger:.2f}, R={self.right_trigger:.2f}"
            )
        elif axis_id == Axes.RIGHT_TRIGGER:
            self.right_trigger = value
            self.trigger_label.setText(
                f"Triggers: L={self.left_trigger:.2f}, R={self.right_trigger:.2f}"
            )


def run():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


class ControllerDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Game Controller Demo")
        self.setGeometry(100, 100, 600, 400)

        # Create central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Status labels
        self.status_label = QLabel("Controller Status: Initializing...")
        self.button_label = QLabel("Last Button: None")
        self.left_stick_label = QLabel("Left Stick: (0.00, 0.00)")
        self.right_stick_label = QLabel("Right Stick: (0.00, 0.00)")
        self.trigger_label = QLabel("Triggers: L=0.00, R=0.00")

        layout.addWidget(self.status_label)
        layout.addWidget(self.button_label)
        layout.addWidget(self.left_stick_label)
        layout.addWidget(self.right_stick_label)
        layout.addWidget(self.trigger_label)

        # Store axis values
        self.left_x = 0.0
        self.left_y = 0.0
        self.right_x = 0.0
        self.right_y = 0.0
        self.left_trigger = 0.0
        self.right_trigger = 0.0

        # Initialize controller thread
        self.controller_thread = ControllerThread(poll_rate=0.01)

        # Connect signals to slots
        self.controller_thread.button_pressed.connect(self.on_button_pressed)
        self.controller_thread.button_released.connect(self.on_button_released)
        self.controller_thread.axis_motion.connect(self.on_axis_motion)
        self.controller_thread.hat_motion.connect(self.on_hat_motion)

        # Start controller thread
        self.controller_thread.start()
        self.status_label.setText("Controller Status: Connected")

    def closeEvent(self, event):
        """Clean up when window closes."""
        self.controller_thread.stop()
        self.controller_thread.wait()
        event.accept()
