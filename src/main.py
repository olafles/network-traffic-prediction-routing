"""Main runner (small test harness).

Edit `SCENARIO` below to change the input folder used by the
simulation. This keeps `main.py` minimal while allowing quick
manual testing.
"""

from simulator import run_simulation

SCENARIO = "110000_0"


if __name__ == "__main__":
    run_simulation(SCENARIO)
