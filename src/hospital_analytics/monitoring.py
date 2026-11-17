from __future__ import annotations

import numpy as np


def probability_reference(probabilities: np.ndarray, bins: int = 10) -> tuple[list[float], list[float]]:
    edges = np.unique(np.quantile(probabilities, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = 0.0, 1.0
    counts, _ = np.histogram(probabilities, bins=edges)
    distribution = counts / max(counts.sum(), 1)
    return edges.tolist(), distribution.tolist()


def population_stability_index(
    current_probabilities: np.ndarray,
    reference_edges: list[float],
    reference_distribution: list[float],
) -> float:
    if len(reference_edges) != len(reference_distribution) + 1:
        raise ValueError("Reference edges and distribution do not have compatible lengths")
    if len(current_probabilities) == 0:
        raise ValueError("At least one probability is required")
    current_counts, _ = np.histogram(current_probabilities, bins=np.asarray(reference_edges))
    current = current_counts / max(current_counts.sum(), 1)
    expected = np.asarray(reference_distribution)
    epsilon = 1e-6
    psi = np.sum((current + epsilon - expected - epsilon) * np.log((current + epsilon) / (expected + epsilon)))
    return round(float(psi), 4)


def drift_status(psi: float) -> str:
    if psi < 0.10:
        return "stable"
    if psi < 0.25:
        return "watch"
    return "investigate"


def monitoring_report(
    probabilities: np.ndarray,
    threshold: float,
    reference_edges: list[float],
    reference_distribution: list[float],
) -> dict[str, float | int | str]:
    """Summarise model-output drift for an incoming appointment batch."""
    values = np.asarray(probabilities, dtype=float)
    psi = population_stability_index(values, reference_edges, reference_distribution)
    return {
        "sample_size": int(values.size),
        "average_probability": round(float(values.mean()), 4),
        "review_rate": round(float((values >= threshold).mean()), 4),
        "psi": psi,
        "status": drift_status(psi),
    }
