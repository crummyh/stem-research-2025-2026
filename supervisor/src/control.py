from turtle import speed

import numpy as np
from numpy.matlib import spacing

from src.config import (
    BODY_RADIUS,
    MAX_CURVE,
    MAX_SPOOL_SPEED,
    MIN_SPOOL_SPEED,
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
    tendon_1 = (c * BODY_RADIUS * np.cos(TENDON_1_ANGLE - d)) / TENDON_SPOOL_RADIUS
    tendon_2 = (c * BODY_RADIUS * np.cos(TENDON_2_ANGLE - d)) / TENDON_SPOOL_RADIUS
    tendon_3 = (c * BODY_RADIUS * np.cos(TENDON_3_ANGLE - d)) / TENDON_SPOOL_RADIUS

    return (tendon_1, tendon_2, tendon_3)


def cartesian_to_polar(x: float, y: float) -> tuple[float, float]:
    rho = np.sqrt(x**2 + y**2)  # R
    phi = np.arctan2(y, x)  # Theta
    return (phi, rho)


def controller_to_tendon(x: float, y: float) -> tuple[float, float, float]:
    x *= MAX_CURVE
    y *= MAX_CURVE

    polar = cartesian_to_polar(x, y)

    return get_tendon_steering(*polar)


# Assumes that left and right are exculusive and between 0 and 1
def controller_to_spool(left: float, right: float, speed_modifier: float) -> float:
    if left != 0 and right != 0:
        raise ValueError("The left and right values must be exclusive")

    result = 0.0
    if right != 0:
        result = speed_modifier * right
    elif left != 0:
        result = -1 * speed_modifier * left  # Invert values on the left
    else:
        result = 0

    if result > MAX_SPOOL_SPEED or result < MIN_SPOOL_SPEED:
        raise ArithmeticError(
            f"Opperation resulted with {result}, which is either larger then the max speed or smaller then the min speed"
        )

    return result
