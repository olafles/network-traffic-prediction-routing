"""Spectrum/Link related stuff"""

from enum import IntEnum
from topology_constants import DISTANCES
from logger import logger

N_NODES = 28  # Number of nodes
N_SLOTS = 320  # Number of slots for each link


class SlotState(IntEnum):
    """Define possible spectrum slot states

    FREE or OCCUPIED"""

    FREE = 0
    OCCUPIED = 1


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
