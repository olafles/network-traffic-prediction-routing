import pickle
import os
from typing import Optional
from pathlib import Path
import numpy as np
from dataclasses import dataclass, field
from collections import deque
from logger import logger

current_dir = Path(__file__).parent
MODEL_PATH = current_dir.parent / "models" / "knn_model.pkl"


class TrafficPredictor:
    def __init__(self):
        with open(MODEL_PATH, "rb") as f:
            self.model = pickle.load(f)

    def predict(self, window: list[list[float]]) -> float:
        """
        window:
        [
            [x0_mean_occ, x0_max_occ, ..., x0_max_frag],
            [x1_mean_occ, x1_max_occ, ..., x1_max_frag],
            [x2_mean_occ, x2_max_occ, ..., x2_max_frag],
        ]
        """
        x = np.array(window).flatten().reshape(1, -1)
        y_hat = self.model.predict(x)[0]
        if y_hat > 1.0:
            logger.critical("Predicted penalty > 1.0: %s", y_hat)
        return float(y_hat)


@dataclass
class NodeSnapshotBuffer:
    """Stores the 10 most recent snapshots for each node."""

    max_snapshots: int = 10
    snapshots_by_node: dict[int, deque] = field(default_factory=dict)

    def add_snapshot(self, node: int, snapshot: any, timestamp: int) -> None:
        """Add a snapshot for a node, maintaining rolling window of max_snapshots."""
        if node not in self.snapshots_by_node:
            self.snapshots_by_node[node] = deque(maxlen=self.max_snapshots)

        self.snapshots_by_node[node].append({"timestamp": timestamp, "data": snapshot})

    def get_node_snapshots(self, node: int) -> list:
        """Get all snapshots for a specific node."""
        if node not in self.snapshots_by_node:
            return []
        return list(self.snapshots_by_node[node])

    def get_latest_snapshot(self, node: int) -> Optional[dict]:
        """Get the most recent snapshot for a node."""
        if node not in self.snapshots_by_node or len(self.snapshots_by_node[node]) == 0:
            return None
        return self.snapshots_by_node[node][-1]

    def get_latest_fifth_and_tenth_snapshots(self, node: int) -> list[list[float]]:
        """Get the latest, 5th, and 10th most recent snapshots for a node.

        Returns a list of snapshot data in format:
        [
            [x0_mean_occ, x0_max_occ, ..., x0_max_frag],  # latest
            [x1_mean_occ, x1_max_occ, ..., x1_max_frag],  # 5th
            [x2_mean_occ, x2_max_occ, ..., x2_max_frag],  # 10th
        ]
        """
        if node not in self.snapshots_by_node or len(self.snapshots_by_node[node]) == 0:
            return []

        snapshots = self.snapshots_by_node[node]
        if len(snapshots) < 10:
            return None

        return [
            snapshots[-1]["data"],
            snapshots[-5]["data"],
            snapshots[-10]["data"],
        ]
