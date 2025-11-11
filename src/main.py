"""Main file"""

from data_loader import DataLoader

d = DataLoader("70000_0")
TRAFFIC = d.export_traffic()
