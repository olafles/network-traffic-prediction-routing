# network-traffic-prediction-routing

## Project Overview
- A university project that implements traffic-aware network routing by forecasting future traffic and using those forecasts to make routing decisions. Goal was to improve routing decisions (link utilization, blocking, fragmentation) by predicting short-term traffic patterns and creating an algorithm to use the predicted values for future routes.

## How to use
- Run the main simulation entrypoint: [src/main.py](src/main.py)

## Repository Layout
- **datasets**: raw and scaled CSV datasets used for training and validation (`train_dataset.csv`, `train_dataset_scaled.csv`, `test_dataset.csv`, `test_dataset_scaled.csv`).
- **models**: trained model file (KNN artifact).
- **network_topology**: network topology files including node list and topology definition (`cities.txt`, `ff.net`).
- **snapshots**: simulation snapshot CSVs containing routing/traffic snapshots recorded during runs.
- **src**: main source code
	- [src/main.py](src/main.py): entrypoint to run simulations and experiments.
	- [src/data_loader.py](src/data_loader.py): dataset loading and preprocessing helpers.
	- [src/predictor.py](src/predictor.py): prediction interface and model wrappers.
	- [src/simulator.py](src/simulator.py): simulation loop and event handling for routing.
	- [src/topology.py](src/topology.py): topology parsing utilities.
	- [src/dijkstra.py](src/dijkstra.py): shortest-path computation used by routing logic.
	- [src/request.py](src/request.py): request representation and validation.
	- [src/spectrum.py](src/spectrum.py): spectrum/allocation utilities for links.
	- [src/logger.py](src/logger.py): logger config to avoid prints.
	- [src/topology_constants.py](src/topology_constants.py): constants for topology and simulation parameters (ex. distance matrix).
- **traffic_data/**: raw traffic time-series files used to build datasets and to feed simulations (organized by folders).
- **training/**: training utilities and scripts
	- `normalize_datasets.py`: scaling/normalization utilities.
	- `sliding_window_builder.py`: transforms time-series into sliding-window feature matrices for training.
	- `train_knn.py`: script to train and evaluate a KNN predictor used by the project.
