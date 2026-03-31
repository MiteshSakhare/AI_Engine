"""
Peer Feature Engineering Pipeline.

Aggregates features across all merchants in the same cluster.

File: backend/pipelines/feature_engineering/peer_features.py
"""

import logging
from typing import Dict, List

logger = logging.getLogger("bravola.pipelines.peer_features")


def compute_peer_medians(
    cluster_merchants: List[Dict[str, float]],
) -> Dict[str, float]:
    """
    Compute median KPI values for a peer cluster.

    Input: list of merchant feature dicts for all merchants in the cluster.
    Output: median of each metric.
    """

    if not cluster_merchants:
        return {}

    import statistics

    all_keys: set[str] = set()
    for m in cluster_merchants:
        all_keys.update(m.keys())

    medians = {}
    for key in all_keys:
        values = [m[key] for m in cluster_merchants if key in m and isinstance(m[key], (int, float))]
        if values:
            medians[key] = float(f"{statistics.median(values):.4f}")

    return medians
