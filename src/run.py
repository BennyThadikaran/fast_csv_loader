import timeit
from datetime import datetime
from csv_loader import csv_loader
import pandas as pd
import os
from pathlib import Path


def read_csv(fpath, end_date=None):
    df = pd.read_csv(fpath, index_col="Date", parse_dates=["Date"])

    if end_date:
        return df.loc[:end_date].iloc[-160:]

    return df.iloc[-160:]


def print_perf(fn, seconds, base_time=None):
    name = fn.__name__ if callable(fn) else fn

    stmt = f"{name: <12} | Time: {seconds:.5f} seconds"
    pct = None

    if base_time:
        pct = get_pct_improvement(base_time, seconds)
        stmt += f" | {pct:.2f}%"

    print(stmt)


def get_pct_improvement(base_time, new_time):
    pct = ((base_time - new_time) / base_time) * 100

    return pct


sym_list = (
    "aartiind",
    "bajajcon",
    "small",
)

dt = datetime(2023, 1, 1)

# First test - Default arguments
print("Load last 160 lines")

for sym in sym_list:
    file_path = Path(f"./test_data/{sym}.csv")

    size = os.path.getsize(file_path) / 1024

    print(f"\n{sym.upper()} | Size: {size:.2f} kb")

    regular_time = timeit.timeit(stmt=lambda: read_csv(file_path), number=100)

    print_perf(read_csv, regular_time)

    ts = timeit.timeit(
        stmt=lambda: csv_loader(file_path),
        number=100,
    )

    print_perf(csv_loader, ts, base_time=regular_time)


# Second test - end_date
print("\nLoad 160 lines upto 1st Jan 2023")

for sym in sym_list:
    file_path = Path(f"./test_data/{sym}.csv")

    size = os.path.getsize(file_path) / 1024

    print(f"\n{sym.upper()} | Size: {size:.2f} kb")

    regular_time = timeit.timeit(
        stmt=lambda: read_csv(file_path, end_date=dt), number=100
    )

    print_perf(read_csv, regular_time)

    ts = timeit.timeit(
        stmt=lambda: csv_loader(file_path, end_date=dt),
        number=100,
    )

    print_perf(csv_loader, ts, base_time=regular_time)
