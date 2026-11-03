"""Calibration / CSI unit tests."""

import numpy as np

from nexus.domain.monitoring import (
    characteristic_stability_index,
    expected_calibration_error,
)


def test_ece_perfect():
    y = np.array([0.0, 0.0, 1.0, 1.0])
    p = np.array([0.0, 0.0, 1.0, 1.0])
    assert expected_calibration_error(y, p, n_bins=4) < 0.05


def test_csi_identical():
    x = np.random.default_rng(0).normal(size=300)
    assert characteristic_stability_index(x, x) < 0.01