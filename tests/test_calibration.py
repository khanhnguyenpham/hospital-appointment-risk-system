import numpy as np
import pytest

from hospital_analytics.train import expected_calibration_error


def test_expected_calibration_error_is_small_for_well_separated_probabilities():
    targets = np.array([0, 0, 1, 1])
    probabilities = np.array([0.05, 0.10, 0.90, 0.95])
    assert expected_calibration_error(targets, probabilities, bins=2) == pytest.approx(0.075)


def test_expected_calibration_error_detects_confident_wrong_predictions():
    targets = np.array([0, 0, 1, 1])
    probabilities = np.array([0.90, 0.80, 0.20, 0.10])
    assert expected_calibration_error(targets, probabilities, bins=2) == pytest.approx(0.85)


def test_expected_calibration_error_validates_inputs():
    with pytest.raises(ValueError):
        expected_calibration_error(np.array([]), np.array([]))
    with pytest.raises(ValueError):
        expected_calibration_error(np.array([0, 1]), np.array([0.2]), bins=1)
