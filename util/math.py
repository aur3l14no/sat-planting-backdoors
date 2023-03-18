import numpy as np
import random


def power_random(low, high, g=-1, size=1):
    """Power-law gen for pdf(x)\propto x^{g-1} for a<=x<=b."""
    r = np.random.random(size=size)
    ag, bg = float(low)**g, float(high)**g
    return (ag + (bg - ag) * r) ** (1./g)

