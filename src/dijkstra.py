"""dijkstra implementation"""

from typing import List
import heapq
from logger import logger

from topology_constants import DISTANCES
from predictor import NodeSnapshotBuffer


def dijkstra(start: int, target: int) -> List[int]:
    """Compute shortest path between start and target nodes using Dijkstra.

    Args:
        start: index of source node (0-based)
        target: index of destination node (0-based)

    Returns:
        A list of node indices representing the path from start to target
        (inclusive). Returns an empty list if target is unreachable.
    """
    logger.debug("Starting dijkstra from %s to %s", start, target)
    n = len(DISTANCES)
    if not (0 <= start < n and 0 <= target < n):
        raise IndexError("start or target node out of range")

    # distances and previous node trackers
    dist = [float("inf")] * n
    prev = [None] * n

    dist[start] = 0
    heap = [(0, start)]  # (distance, node)

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == target:
            break

        row = DISTANCES[u]
        # iterate neighbors
        for v, w in enumerate(row):
            if not w:
                continue  # 0 indicates no edge
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    # No path found
    if dist[target] == float("inf"):
        logger.critical("dijkstra couldn't find path %s -> %s", start, target)
        return []

    # Reconstruct path
    path: List[int] = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path


def advanced_dijkstra(
    start: int,
    target: int,
    node_penalty,
    gamma: float = 1.0,
) -> list[int]:

    n = len(DISTANCES)
    dist = [float("inf")] * n
    prev = [None] * n

    dist[start] = 0
    heap = [(0, start)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        if u == target:
            break

        for v, w in enumerate(DISTANCES[u]):
            if not w:
                continue

            #  This is where KNN output is used
            penalty_u = node_penalty.get(u, 0.0)
            nd = d + w * (1 + gamma * penalty_u)

            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    if dist[target] == float("inf"):
        return []

    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    return path[::-1]
