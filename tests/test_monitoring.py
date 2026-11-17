import numpy as np

from hospital_analytics.monitoring import (
    drift_status,
    monitoring_report,
    population_stability_index,
    probability_reference,
)


def test_same_distribution_has_low_psi():
    probabilities = np.linspace(0.02, 0.98, 500)
    edges, reference = probability_reference(probabilities)
    psi = population_stability_index(probabilities, edges, reference)
    assert psi < 0.01
    assert drift_status(psi) == "stable"


def test_shifted_distribution_is_flagged():
    reference_values = np.linspace(0.02, 0.60, 500)
    edges, reference = probability_reference(reference_values)
    shifted = np.linspace(0.50, 0.98, 500)
    assert drift_status(population_stability_index(shifted, edges, reference)) == "investigate"


def test_monitoring_report_includes_operational_rate():
    reference_values = np.linspace(0.05, 0.75, 500)
    edges, reference = probability_reference(reference_values)
    report = monitoring_report(reference_values, 0.50, edges, reference)
    assert report["sample_size"] == 500
    assert 0 < report["review_rate"] < 1
    assert report["status"] == "stable"
