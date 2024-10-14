import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "csv_loader"))

from csv_loader import csv_loader
