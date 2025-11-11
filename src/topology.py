"""Helper methods related to topology/geography to avoid direct array access"""

from topology_constants import CITIES, DISTANCES


class TopologyData:

    @classmethod
    def get_city_name(cls, city_id: int) -> str:
        try:
            return CITIES[city_id]["name"]
        except IndexError:
            raise IndexError(f"Invalid city ID: {city_id=}. ID out of bounds.")
        except TypeError:
            raise TypeError("City ID must be an int.")

    @classmethod
    def get_distance(cls, src: int, dst: int) -> int:
        try:
            distance = DISTANCES[src][dst]
            return distance
        except IndexError:
            raise IndexError(f"Invalid city ID: {src=} or {dst=}.")
        except TypeError:
            raise TypeError("City IDs must be integers.")

    @classmethod
    def get_country(cls, city_identifier: int | str) -> str:

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
