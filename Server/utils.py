import numpy as np

def toFeet(x):
    """converts from meters to feets"""
    return x * 3.2808399

def toHomogeneous(rvec, tvec):
    """converts tranform's representation by pair of rvec(3x3) and tvec(3x1) 
    to homogeneous representation (4x4)
        |r11 r12 r13 t11|
        |r21 r22 r23 t21|
        |r31 r32 r33 t31|
        | 0   0   0   1 |
    """

    return np.vstack((np.hstack((rvec, tvec)), np.asarray([[0, 0, 0, 1]])))
