"""Helper methods related to topology/geography to avoid direct array access"""

from topology_constants import CITIES, DISTANCES
from logger import logger


class TopologyData:

    @classmethod
    def get_city_name(cls, city_id: int) -> str:
        """Return city name for given index

        Args:
            city_id (int): index of city

        Raises:
            IndexError: Out of bounds
            TypeError: Wrong type passed

        Returns:
            str: City name string
        """
        try:
            return CITIES[city_id]["name"]
        except IndexError:
            raise IndexError(f"Invalid city ID: {city_id=}. ID out of bounds.")
        except TypeError:
            raise TypeError("City ID must be an int.")

    @classmethod
    def get_distance(cls, src: int, dst: int) -> int:
        """Return distance between 2 nodes.

        If 0 is returned there is no link between these nodes.

        Args:
            src (int): Source node index
            dst (int): Destination node index

        Raises:
            IndexError: Out of bounds
            TypeError: Wrong type passed

        Returns:
            int: Distance
        """
        try:
            distance = DISTANCES[src][dst]
            return distance
        except IndexError:
            raise IndexError(f"Invalid city ID: {src=} or {dst=}.")
        except TypeError:
            raise TypeError("City IDs must be integers.")

    @classmethod
    def get_country(cls, city_identifier: int | str) -> str:
        """Return country name based on index/name of city

        Args:
            city_identifier (int | str): Index or city name

        Raises:
            IndexError: Out of bounds
            ValueError: City name not found
            TypeError: Invalid type of input

        Returns:
            str: Country name
        """

        # ID(int) passed:
        if isinstance(city_identifier, int):
            try:
                return CITIES[city_identifier]["country"]
            except IndexError:
                raise IndexError(f"Invalid city ID: {city_identifier=}.")

        # name(str) passed:
        elif isinstance(city_identifier, str):
            search_name = city_identifier.lower()
            for city in CITIES:
                if city["name"].lower() == search_name:
                    return city["country"]
            raise ValueError(f"City name not found: {city_identifier=}")

        # Anything else:
        else:
            raise TypeError(f"Invalid type {type(city_identifier).__name__}.")

    @classmethod
    def get_max_distance_from_path(cls, path: list[int]) -> int:
        """Returns longest distance from distances between path nodes

        Usage:
            path = [5, 6, 8, 7, 11, 25, 26]
            print(TopologyData.get_max_distance_from_path(path))

        Args:
            path (list[int]): List of nodes visited

        Returns:
            int: Maximum distance from path
        """
        values: list[int] = []
        for i in range(len(path) - 1):
            distance = cls.get_distance(path[i], path[i + 1])
            if distance == 0:
                logger.critical("Path contains 0km distance")
            values.append(distance)

        return max(values) if values else 0

    @classmethod
    def get_path_total_distance(cls, path: list[int]) -> int:
        """Returns total distance of the path (sum of consecutive link distances).

        The project specification requires choosing modulation according to the
        full path length (total distance), not the longest single link. This
        helper computes that sum so the simulator can select an appropriate
        modulation.
        """
        total = 0
        for i in range(len(path) - 1):
            distance = cls.get_distance(path[i], path[i + 1])
            if distance == 0:
                logger.critical(
                    "Path contains 0km distance between %s->%s",
                    path[i],
                    path[i + 1],
                )
            total += distance

        return total
