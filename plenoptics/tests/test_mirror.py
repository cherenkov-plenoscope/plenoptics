import plenoptics
import numpy as np


def zzz(x, y):
    return np.hypot(x, y)


def test_init_mirror_deformations():

    xs = np.linspace(-2, 2, 5)
    ys = np.linspace(-2, 2, 5)

    z_map = np.zeros(shape=(5, 5))
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            z_map[ix, iy] = zzz(x=x, y=y)

    dm = plenoptics.instruments.mirror.deformation_map.init_from_z_map(
        z_map=z_map,
        mirror_diameter_m=4.0,
    )

    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):

            z_m = plenoptics.instruments.mirror.deformation_map.evaluate(
                deformation_map=dm,
                x_m=x,
                y_m=y,
            )

            assert abs(zzz(x=x, y=y) - z_m) < 0.4
