"""Spectrum/Link related stuff"""

from enum import IntEnum
from topology_constants import DISTANCES
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
                logger.error("Tried to release on non-existent link %s->%s", u, v)
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
