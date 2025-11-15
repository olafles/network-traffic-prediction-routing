# TODO

### Implement SpectrumManager 

Implement `SpectrumManager` class in `spectrum.py` to allow operations on links/spectrum like:
* **Check**, **free** and **occupy** slots on given link
* Check if *spectrum continuity* is possible on some *path* 

Most likely it might be a good idea to treat *path* as an array of nodes **OR** create a structure containing:
```python
 path: List[int]  # nodes from start to finish
 start_slot: int  # first occupied slot of spectrum
 nslots: int      # number of slots needed for bandwidth/modulation
 ```
 This could be useful for later encapsulation in ***Connection***(?) class to keep track of connections over time units and clear slots after required time for each connection has passed

 ### Dijkstra -> FirstFit

 ~~Implement dijkstra~~ **DONE**, then use spectrummanager's "check spectrum continuity" to decide whether request can be accepted or has to be rejected. If there is no free, continous spectrum on the shortest path the request should be rejected.
