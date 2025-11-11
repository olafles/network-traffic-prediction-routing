"""Class representing a single traffic request in the network"""

from dataclasses import dataclass


@dataclass(slots=True)
class Request:
    """Dataclass to represent a single request"""

    start: int  # Starting node (0-27)
    end: int  # Destination node (0-27)
    size_gbps: float  # Bandwidth required
    duration: int  # How many time units it needs
    arrival_time: int  # What time unit does it arrive in
    # arrival_time might not be needed due to possible redundancy by list index


def validate_request(rq: Request) -> None:
    """Validates a Request object and raises ValueError if invalid."""

    # Validate ranges
    if not (0 <= rq.start <= 27):
        raise ValueError(f"start must be 0–27, got {rq.start}")

    if not (0 <= rq.end <= 27):
        raise ValueError(f"end must be 0–27, got {rq.end}")

    # Validate start != end
    if rq.start == rq.end:
        raise ValueError(f"start and end must difffer: {rq.start=} {rq.end=}")

    # Validate size
    if rq.size_gbps <= 0:
        raise ValueError(f"size_gbps must be > 0, got {rq.size_gbps}")

    # Validate duration
    if rq.duration <= 0:
        raise ValueError(f"duration must be > 0, got {rq.duration}")

    # Validate arrival time
    if rq.arrival_time < 0 or rq.arrival_time >= 1000:
        raise ValueError(f"arrival_time must be 0-999, got {rq.arrival_time}")
