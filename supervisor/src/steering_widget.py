import math

from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPalette, QPen, QPolygonF
from PyQt6.QtWidgets import QSizePolicy, QWidget

from src.config import V_TENDON_1_ANGLE, V_TENDON_2_ANGLE, V_TENDON_3_ANGLE


class RobotSteeringWidget(QWidget):
    """
    A custom PyQt6 widget that displays a top-down view of a vine robot
    with three tendons and visualizes the steering direction.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)

        # Set size policy to expand but maintain aspect ratio
        self.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.MinimumExpanding,
        )

        # Tendon angles (in radians, from positive x-axis)
        self._tendon_1_angle = V_TENDON_1_ANGLE
        self._tendon_2_angle = V_TENDON_2_ANGLE
        self._tendon_3_angle = V_TENDON_3_ANGLE

        # Tendon values (motor positions in radians)
        self._tendon_1_value = 0.0
        self._tendon_2_value = 0.0
        self._tendon_3_value = 0.0

        # Steering direction and magnitude
        self._steering_angle = 0.0  # radians
        self._steering_magnitude = 0.0  # 0 to 1

        # Visual properties
        self._body_radius_ratio = 0.35  # Ratio of widget size
        self._tendon_length_ratio = 0.45

    def heightForWidth(self, a0):
        return a0

    def hasHeightForWidth(self):
        return True

    def sizeHint(self):
        return QSize(360, 360)

    def setTendon1Value(self, value):
        self._tendon_1_value = value
        self.update()

    def setTendon2Value(self, value):
        self._tendon_2_value = value
        self.update()

    def setTendon3Value(self, value):
        self._tendon_3_value = value
        self.update()

    def setSteeringAngle(self, value):
        self._steering_angle = value
        self.update()

    def setSteeringMagnitude(self, value):
        self._steering_magnitude = max(0.0, min(1.0, value))
        self.update()

    def setTendonValues(self, t1, t2, t3):
        self._tendon_1_value = t1
        self._tendon_2_value = t2
        self._tendon_3_value = t3
        self.update()

    def setSteering(self, angle, magnitude):
        self._steering_angle = angle
        self._steering_magnitude = max(0.0, min(1.0, magnitude))
        self.update()

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate center and radius
        size = min(self.width(), self.height())
        center_x = self.width() / 2
        center_y = self.height() / 2
        body_radius = size * self._body_radius_ratio
        tendon_radius = size * self._tendon_length_ratio

        # Draw body circle
        painter.setPen(QPen(self.palette().light().color(), 2))
        painter.setBrush(QBrush(self.palette().alternateBase().color()))
        painter.drawEllipse(QPointF(center_x, center_y), body_radius, body_radius)

        # Draw tendons
        self._draw_tendon(
            painter,
            center_x,
            center_y,
            body_radius,
            tendon_radius,
            self._tendon_1_angle,
            self._tendon_1_value,
            self.palette().highlight().color(),
            "T1",
        )
        self._draw_tendon(
            painter,
            center_x,
            center_y,
            body_radius,
            tendon_radius,
            self._tendon_2_angle,
            self._tendon_2_value,
            self.palette().highlight().color(),
            "T2",
        )
        self._draw_tendon(
            painter,
            center_x,
            center_y,
            body_radius,
            tendon_radius,
            self._tendon_3_angle,
            self._tendon_3_value,
            self.palette().highlight().color(),
            "T3",
        )

        # Draw steering direction arrow if magnitude > 0
        if self._steering_magnitude > 0.01:
            self._draw_steering_arrow(painter, center_x, center_y, body_radius * 0.7)

    def _draw_tendon(
        self, painter, cx, cy, body_r, tendon_r, angle, value, color, label
    ):
        """Draw a single tendon with its line, circle, and label."""
        # Convert angle to Qt coordinate system (y-axis is inverted)
        qt_angle = angle - math.pi / 2

        # Calculate positions
        body_x = cx + body_r * math.cos(qt_angle)
        body_y = cy + body_r * math.sin(qt_angle)
        tendon_x = cx + tendon_r * math.cos(qt_angle)
        tendon_y = cy + tendon_r * math.sin(qt_angle)
        label_x = cx + (tendon_r + 20) * math.cos(qt_angle)
        label_y = cy + (tendon_r + 20) * math.sin(qt_angle)

        # Determine line width based on tendon value (thicker = more tension)
        base_width = 3
        value_width = max(0, min(5, abs(value) * 2))  # Scale value to width
        line_width = base_width + value_width

        # Draw line from center to body edge
        painter.setPen(QPen(color, line_width))
        painter.drawLine(QPointF(cx, cy), QPointF(body_x, body_y))

        # Draw tendon circle
        circle_radius = 16
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(tendon_x, tendon_y), circle_radius, circle_radius)

        # Draw label
        painter.setPen(QPen(Qt.GlobalColor.white))
        # painter.drawText(int(label_x - 10), int(label_y + 5), label)
        painter.drawText(int(label_x - 10), int(label_y + 5), label)

        # Draw value text inside or near the circle
        painter.setPen(QPen(Qt.GlobalColor.white))
        value_text = f"{value:.2f}"
        # For small values, draw text next to circle
        if abs(value) < 0.3:
            text_offset = 15
            text_x = tendon_x + text_offset * math.cos(qt_angle)
            text_y = tendon_y + text_offset * math.sin(qt_angle)
        else:
            text_x = tendon_x
            text_y = tendon_y

        # Calculate text bounds for centering (approximate)
        text_width = len(value_text) * 7
        painter.drawText(int(text_x - text_width / 2), int(text_y + 4), value_text)

    def _draw_steering_arrow(self, painter, cx, cy, length):
        """Draw an arrow indicating the steering direction."""
        # Convert angle to Qt coordinate system
        qt_angle = self._steering_angle - math.pi / 2

        # Calculate arrow end point (scaled by magnitude)
        arrow_length = length * self._steering_magnitude
        end_x = cx + arrow_length * math.cos(qt_angle)
        end_y = cy + arrow_length * math.sin(qt_angle)

        # Draw arrow line
        painter.setPen(QPen(QColor(59, 130, 246), 3))
        painter.drawLine(QPointF(cx, cy), QPointF(end_x, end_y))

        # Draw arrowhead
        arrow_size = 12
        angle1 = qt_angle + math.pi - math.pi / 6
        angle2 = qt_angle + math.pi + math.pi / 6

        p1_x = end_x + arrow_size * math.cos(angle1)
        p1_y = end_y + arrow_size * math.sin(angle1)
        p2_x = end_x + arrow_size * math.cos(angle2)
        p2_y = end_y + arrow_size * math.sin(angle2)

        arrow_polygon = QPolygonF(
            [QPointF(end_x, end_y), QPointF(p1_x, p1_y), QPointF(p2_x, p2_y)]
        )

        painter.setBrush(QBrush(QColor(59, 130, 246)))
        painter.drawPolygon(arrow_polygon)
