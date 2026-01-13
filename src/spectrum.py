"""Spectrum/Link related stuff"""

from enum import IntEnum
from pathlib import Path
import csv
from topology_constants import DISTANCES, NEIGHBOURS
from logger import logger
from typing import NamedTuple

N_NODES = 28  # Number of nodes
N_SLOTS = 320  # Number of slots for each link


class SlotState(IntEnum):
    """Define possible spectrum slot states

    FREE or OCCUPIED"""

    FREE = 0
    OCCUPIED = 1


class Modulation(NamedTuple):
    """Typed named tuple for modulation entries.

    This is a subclass of tuple so index-based access still works
    (e.g. MODULATIONS[0][1] == 50) while also providing attribute access
    (MODULATIONS[0].max_bitrate).
    """

    name: str
    max_bitrate: int
    max_distance: int


# Format: (name, max_bitrate, max_distance)
MODULATIONS: list[Modulation] = [
    Modulation("BPSK", 50, 6300),
    Modulation("QPSK", 100, 3500),
    Modulation("16QAM", 150, 1200),
    Modulation("32QAM", 200, 600),
]


def _get_spectrum_state_array() -> list[list[list[int] | None]]:
    """Generate initial spectrum state representation array

    Works like DISTANCES matrix but this one is 2.5D because if a link exists
    it has an array of slots (320 spaces). If not it has None.

    Links are unidirectional so arr[n][m] != arr[m][n]

    Returns:
        list[list[list[int] | None]]: array representing freq. slots/links
    """
    logger.debug("Generating spectrum matrix")
    spectrum_state = []
    for i in range(N_NODES):
        row = []
        for j in range(N_NODES):

            #  Check if link exists (distance != 0)
            if DISTANCES[i][j] > 0:
                #  Create an "slots" array
                link_slots = [SlotState.FREE] * N_SLOTS
                row.append(link_slots)
            else:
                # Mark non existent links as None
                # Needs validation! but saves 224640
                # values from being in memory :)
                row.append(None)

        spectrum_state.append(row)
    return spectrum_state


class Allocation(NamedTuple):
    """Represents an allocation so it can be released later."""

    id: int
    path: list[int]
    start_slot: int
    n_slots: int


class SpectrumManager:
    """Manage spectrum state: find first-fit, reserve and release allocations."""

    def __init__(self) -> None:
        self._state = _get_spectrum_state_array()
        self._next_id = 1

    def find_first_fit(self, path: list[int], n_slots: int) -> int | None:
        """Return start slot index for first-fit or None if not found."""
        if n_slots <= 0 or n_slots > N_SLOTS:
            return None

        links = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            link = self._state[u][v]
            if link is None:
                return None
            links.append(link)

        last_start = N_SLOTS - n_slots
        for start in range(0, last_start + 1):
            ok = True
            for link in links:
                for s in range(start, start + n_slots):
                    if link[s] != SlotState.FREE:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return start

        return None

    def reserve_slots(
        self, path: list[int], start_slot: int, n_slots: int
    ) -> Allocation:
        """Reserve slots across all links in path and return Allocation."""
        alloc_id = self._next_id
        self._next_id += 1

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            link = self._state[u][v]
            for s in range(start_slot, start_slot + n_slots):
                link[s] = SlotState.OCCUPIED

        return Allocation(alloc_id, path, start_slot, n_slots)

    def release(self, allocation: Allocation) -> None:
        """Release previously reserved allocation."""
        for i in range(len(allocation.path) - 1):
            u, v = allocation.path[i], allocation.path[i + 1]
            link = self._state[u][v]
            if link is None:
                logger.critical("Tried to release on non-existent link %s->%s", u, v)
                continue
            for s in range(
                allocation.start_slot, allocation.start_slot + allocation.n_slots
            ):
                link[s] = SlotState.FREE

    def debug_free_slots_on_link(self, u: int, v: int) -> int:
        """Return count of free slots on a link (debug helper)."""
        link = self._state[u][v]
        if link is None:
            return 0
        return sum(1 for s in link if s == SlotState.FREE)


class SpectrumAnalyzer:
    def __init__(self, spectrum_manager: SpectrumManager):
        self.state_reference = spectrum_manager._state
        self.neighbours = NEIGHBOURS

    def link_occupancy(self, u: int, v: int) -> float:
        """Return occupancy ratio (0.0-1.0) for link u->v."""
        link = self.state_reference[u][v]
        if link is None:
            logger.critical("Link %s->%s does not exist", u, v)
            return 0.0
        occupied = sum(1 for s in link if s == SlotState.OCCUPIED)
        return occupied / N_SLOTS

    def largest_free_block(self, u: int, v: int) -> int:
        """Return size of largest contiguous free slot block on link u->v."""
        link = self.state_reference[u][v]
        if link is None:
            logger.critical("Link %s->%s does not exist", u, v)
            return 0

        max_block = 0
        current_block = 0

        for slot in link:
            if slot == SlotState.FREE:
                current_block += 1
                max_block = max(max_block, current_block)
            else:
                current_block = 0

        return max_block

    def calculate_fragmentation_index(self, u: int, v: int) -> float:
        """Calculate and return fragmentation index for link u->v."""
        link = self.state_reference[u][v]
        if link is None:
            logger.critical("Link %s->%s does not exist", u, v)
            return 0.0

        total_free_slots = sum(1 for s in link if s == SlotState.FREE)
        largest_block = self.largest_free_block(u, v)

        if total_free_slots == 0:
            return float(1)

        fragmentation_index = 1 - (largest_block / total_free_slots)
        return fragmentation_index

    def node_feature_snapshot(self, time: int, node: int) -> list[float]:
        """
        Return node-level aggregated spectrum features for given node at given time.

        Features (in order):
        - mean occupancy of outgoing links
        - max occupancy of outgoing links
        - min largest free block among outgoing links
        - mean fragmentation
        - max fragmentation
        """

        occupancies = []
        largest_blocks = []
        fragmentations = []

        for neigh in self.neighbours[node]:
            occ = self.link_occupancy(node, neigh)
            lfb = self.largest_free_block(node, neigh)
            frag = self.calculate_fragmentation_index(node, neigh)

            occupancies.append(occ)
            largest_blocks.append(lfb)
            fragmentations.append(frag)

        if not occupancies:
            logger.critical("Node %s has no outgoing links.", node)
            return [0.0, 0.0, 0.0, 0.0, 0.0]

        return [
            sum(occupancies) / len(occupancies),  # mean occupancy
            max(occupancies),  # max occupancy
            min(largest_blocks),  # worst largest free block
            sum(fragmentations) / len(fragmentations),  # mean fragmentation
            max(fragmentations),  # worst fragmentation
        ]


class CsvSnapshotSaver:
    """Simple CSV saver for node feature snapshots.

    Usage: create with a path and call `save_snapshot(snapshot)` where
    `snapshot` is the list returned by `node_feature_snapshot`.
    """

    FIELDNAMES = [
        "time",
        "node",
        "mean_occupancy",
        "max_occupancy",
        "min_largest_free_block",
        "mean_fragmentation",
        "max_fragmentation",
    ]

    def __init__(self, filepath: str | Path) -> None:
        self.path = Path(filepath)
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

        new_file = not self.path.exists()
        # Keep file open for life of the instance to avoid reopen cost.
        self._file = self.path.open("a", newline="")
        self._writer = csv.writer(self._file)
        if new_file:
            self._writer.writerow(self.FIELDNAMES)
            self._file.flush()

    def save_snapshot(self, snapshot: list[float]) -> None:
        """Append a snapshot row to the CSV file using the kept-open file.

        Accepts the list produced by `node_feature_snapshot`.
        """
        vals = list(snapshot)
        if len(vals) < len(self.FIELDNAMES):
            vals += [""] * (len(self.FIELDNAMES) - len(vals))
        else:
            vals = vals[: len(self.FIELDNAMES)]

        rounded = []
        for v in vals:
            if isinstance(v, float):
                rounded.append(round(v, 4))
            else:
                rounded.append(v)

        try:
            self._writer.writerow(rounded)
            self._file.flush()
        except Exception:
            logger.exception("Failed to write snapshot to %s", self.path)

    def close(self) -> None:
        """Close the underlying file if open."""
        try:
            if hasattr(self, "_file") and not self._file.closed:
                self._file.close()
        except Exception:
            logger.exception("Failed to close snapshot file %s", self.path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
