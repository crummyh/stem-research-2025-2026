from math import atan, cos, pi, sqrt

from config import (
    BODY_RADIUS,
    MAX_CURVE,
    TENDON_1_ANGLE,
    TENDON_2_ANGLE,
    TENDON_3_ANGLE,
    TENDON_SPOOL_RADIUS,
)


def get_tendon_steering(c: float, d: float) -> tuple[float, float, float]:
    """
    Takes the designed curvature (c) in radians per meter,
    and the direction (d) in radians, and returns the required
    relative motor positions (in radians).
    """
    tendon_1 = (c * BODY_RADIUS * cos(TENDON_1_ANGLE - d)) / (
        TENDON_SPOOL_RADIUS * pi * pi
    )
    tendon_2 = (c * BODY_RADIUS * cos(TENDON_2_ANGLE - d)) / (
        TENDON_SPOOL_RADIUS * pi * pi
    )
    tendon_3 = (c * BODY_RADIUS * cos(TENDON_3_ANGLE - d)) / (
        TENDON_SPOOL_RADIUS * pi * pi
    )

    return (tendon_1, tendon_2, tendon_3)


def cartesian_to_polar(x: float, y: float) -> tuple[float, float]:
    r = sqrt(x**2 + y**2)
    theta = atan(y / x)

    return (r, theta)


def controller_to_tendon(x: float, y: float) -> tuple[float, float, float]:
    x *= MAX_CURVE
    y *= MAX_CURVE

    polar = cartesian_to_polar(x, y)

    return get_tendon_steering(*polar)
