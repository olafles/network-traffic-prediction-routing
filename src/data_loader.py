"""Data loader for network traffic request dataset"""

import time
from pathlib import Path

from request import Request, validate_request
from logger import logger

N_ITERATIONS = 1000


class DataLoader:
    """DataLoader class to handle reading files from data folders"""

    def __init__(self, folder_name: str) -> None:
        """Initialize DataLoader class to read scenario related data

        Args:
            folder_name (str): "scenario" folder ex. "70000_0"

        Raises:
            FileNotFoundError: Incorrect folder name
        """
        self._folder_name = folder_name
        self._traffic = [
            [] for _ in range(N_ITERATIONS)
        ]  # traffic[5][10] means 11th Request from 6th timeframe

        # data directory: repo root / traffic_data / <folder_name>
        repo_root = Path(__file__).resolve().parents[1]
        self._data_dir = repo_root / "traffic_data" / folder_name
        logger.info("data_dir = %s", self._data_dir)
        if not self._data_dir.exists():
            logger.error("Data directory does not exist: %s", self._data_dir)
            raise FileNotFoundError()

        self._read_whole_folder()
        self._validate_data()
        self._used = False

    def _read_single_file(self, file_index: int) -> None:
        with (self._data_dir / f"{file_index}.txt").open("r") as file:
            for line in file:
                start_node, dest_node, bw, duration = map(float, line.split())
                req = Request(
                    start=start_node,
                    end=dest_node,
                    size_gbps=bw,
                    duration=duration,
                    arrival_time=file_index,
                )
                self._traffic[file_index].append(req)

    def _read_whole_folder(self) -> None:
        logger.info("Reading input files")
        _start_time = time.time()
        for i in range(N_ITERATIONS):
            logger.debug("Reading file %s", i)
            self._read_single_file(i)
        _time_taken = time.time() - _start_time
        logger.info("Reading complete in %.3f seconds", _time_taken)

    def _validate_data(self) -> None:
        counter = 0
        logger.info("Validating imported data")
        _start_time = time.time()

        for i in range(N_ITERATIONS):
            logger.debug("Checking timeframe %s", i)
            for rq in self._traffic[i]:
                validate_request(rq)
                counter += 1

        _time_taken = time.time() - _start_time
        logger.info("Validation complete in %.3f seconds", _time_taken)
        logger.info("Number of requests %s", counter)

        data = 0
        logger.debug("Checking total data")
        for i in range(N_ITERATIONS):
            for rq in self._traffic[i]:
                data += rq.size_gbps * rq.duration
        logger.debug("Total data size: %s", data)

    def export_traffic(self) -> list[list[Request]]:
        """Returns the loaded traffic data and clears it from the
        object to free memory by allowing garbage collection. After
        this call, self._traffic is set to None.

        Raises:
            RuntimeError: Method was already used

        Returns:
            list[list[Request]]: List containing requests for each
                timeframe
        """
        if self._used:
            raise RuntimeError("Traffic was already exported")
        self._used = True
        traffic_data = self._traffic
        self._traffic = None  # clear reference to allow garbage collection
        logger.debug("_traffic attribute is nulled")
        return traffic_data
