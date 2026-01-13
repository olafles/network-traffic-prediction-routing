"""Simulation runner moved out of main.py.

Provides `run_simulation` entrypoint using first-fit allocator and
shortest paths. This keeps `main.py` minimal.
"""

from math import ceil
from typing import Optional
from dataclasses import dataclass, field
from collections import deque
import time
from datetime import datetime
from data_loader import DataLoader, N_ITERATIONS
from predictor import TrafficPredictor, NodeSnapshotBuffer
from dijkstra import dijkstra, advanced_dijkstra
from topology import TopologyData
from spectrum import (
    SpectrumManager,
    MODULATIONS,
    SpectrumAnalyzer,
    CsvSnapshotSaver,
    N_NODES,
)
from logger import logger


def choose_modulation(
    max_path_distance: int, size_gbps: float
) -> tuple[Optional[object], Optional[int]]:
    """Choose modulation that supports path distance and minimizes slots.

    Returns tuple (modulation, n_slots) or (None, None) if impossible.
    """
    candidates = []
    for mod in MODULATIONS:
        if mod.max_distance >= max_path_distance:
            slots = ceil(size_gbps / mod.max_bitrate) * 3
            candidates.append((slots, mod))

    if not candidates:
        return None, None

    candidates.sort(key=lambda x: (x[0], -x[1].max_bitrate))
    best_slots, best_mod = candidates[0]
    return best_mod, int(best_slots)


def run_simulation(
    scenario: str = "70000_0", use_predictor: bool = True, gamma: float = 30.0
) -> list:
    """Run network traffic simulation with optional ML-based routing prediction.

    Args:
        scenario: Traffic scenario identifier (default: "70000_0")
        use_predictor: Whether to use ML predictor for routing (default: False)
        gamma: Weight for predicted node penalties in KNN routing (suggested ~30) (default: 0.0)

    Returns:
        List containing [scenario, gamma, blocking_ratio]
    """
    start_time = time.perf_counter()

    dl = DataLoader(scenario)
    traffic = dl.export_traffic()

    spectrum = SpectrumManager()
    analyzer = SpectrumAnalyzer(spectrum)
    predictor = TrafficPredictor()
    node_snapshot_buffer = (
        NodeSnapshotBuffer()
    )  # This stores last 10 time slot snapshots per node

    # SNAPSHOT_INTERVAL = 5
    # timestamp = datetime.now().strftime("%d_%m-%H-%M-%S")
    # snapshot_saver = CsvSnapshotSaver(f"snapshots/{scenario}.csv") # Only viable for generating training data

    active_allocations: list[dict] = []  # dicts with keys: end_time, allocation, req

    total = 0
    blocked = 0
    accepted = 0

    for t in range(N_ITERATIONS):
        logger.debug("Simulation time %s", t)
        # release allocations that end now
        to_release = [a for a in active_allocations if a["end_time"] <= t]
        for a in to_release:
            spectrum.release(a["allocation"])
            active_allocations.remove(a)

        if use_predictor:
            # We cache link penalties before each time step to save thousands of calls
            # to the predictor during dijkstra.
            for node in range(N_NODES):
                snapshot = analyzer.node_feature_snapshot(t, node)
                node_snapshot_buffer.add_snapshot(node, snapshot, t)

            node_penalty = {}

            for node in range(N_NODES):
                window = node_snapshot_buffer.get_latest_fifth_and_tenth_snapshots(node)
                if window is None:
                    node_penalty[node] = 0.0
                else:
                    node_penalty[node] = predictor.predict(window)

        # process arrivals
        for req in traffic[t]:
            total += 1
            if not use_predictor:
                # FF Only
                path = dijkstra(req.start, req.end)
            else:
                # KNN + FF
                path = advanced_dijkstra(req.start, req.end, node_penalty, gamma=gamma)
            if not path:
                blocked += 1
                continue

            path_dist = TopologyData.get_path_total_distance(path)
            mod, n_slots = choose_modulation(path_dist, req.size_gbps)
            if mod is None:
                blocked += 1
                continue

            start_slot = spectrum.find_first_fit(path, n_slots)
            if start_slot is None:
                blocked += 1
                continue

            allocation = spectrum.reserve_slots(path, start_slot, n_slots)
            active_allocations.append(
                {
                    "end_time": t + req.duration,
                    "allocation": allocation,
                    "req": req,
                }
            )
            accepted += 1

        if t % 100 == 0:
            logger.info(
                "Time %s: total=%s accepted=%s blocked=%s active=%s",
                t,
                total,
                accepted,
                blocked,
                len(active_allocations),
            )
        elif t % 10 == 0:
            logger.info("Simulation time %s", t)

    print("Simulation finished")
    print(f"Total requests: {total}")
    print(f"Accepted: {accepted}")
    print(f"Blocked: {blocked}")
    print(f"Blocking ratio: {blocked / total if total else 0:.4f}")
    elapsed = time.perf_counter() - start_time

    # Format time as H:MM:SS
    m, s = divmod(elapsed, 60)
    h, m = divmod(m, 60)

    print(f"Elapsed time: {elapsed:.3f} s ({int(h)}:{int(m):02d}:{int(s):02d})")
    return [scenario, gamma, blocked / total if total else 0]


if __name__ == "__main__":
    run_simulation()
