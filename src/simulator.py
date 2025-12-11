"""Simulation runner moved out of main.py.

Provides `run_simulation` entrypoint using first-fit allocator and
shortest paths. This keeps `main.py` minimal as before.
"""

from math import ceil
from typing import Optional
import time

from data_loader import DataLoader, N_ITERATIONS
from dijkstra import dijkstra
from topology import TopologyData
from spectrum import SpectrumManager, MODULATIONS
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


def run_simulation(scenario: str = "70000_0") -> None:
    start_time = time.perf_counter()

    dl = DataLoader(scenario)
    traffic = dl.export_traffic()

    spectrum = SpectrumManager()

    active_allocations: list[dict] = []  # dicts with keys: end_time, allocation, req

    total = 0
    blocked = 0
    accepted = 0

    for t in range(N_ITERATIONS):
        # release allocations that end now
        to_release = [a for a in active_allocations if a["end_time"] <= t]
        for a in to_release:
            spectrum.release(a["allocation"])
            active_allocations.remove(a)

        # process arrivals
        for req in traffic[t]:
            total += 1
            path = dijkstra(req.start, req.end)
            if not path:
                blocked += 1
                continue

            max_dist = TopologyData.get_max_distance_from_path(path)
            mod, n_slots = choose_modulation(max_dist, req.size_gbps)
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

    print("Simulation finished")
    print(f"Total requests: {total}")
    print(f"Accepted: {accepted}")
    print(f"Blocked: {blocked}")
    print(f"Blocking ratio: {blocked / total if total else 0:.4f}")
    elapsed = time.perf_counter() - start_time
    # Format elapsed as H:MM:SS
    m, s = divmod(elapsed, 60)
    h, m = divmod(m, 60)
    print(f"Elapsed time: {elapsed:.3f} s ({int(h)}:{int(m):02d}:{int(s):02d})")


if __name__ == "__main__":
    run_simulation()
