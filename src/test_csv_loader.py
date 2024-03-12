import os
import io
import pandas as pd
from datetime import datetime
from tempfile import NamedTemporaryFile
from csv_loader import csv_loader
from pathlib import Path
import unittest


class Test_csv_loader(unittest.TestCase):

    data = "Date,\n2023-12-20,\n2023-12-21,\n2023-12-22,\n2023-12-23,\n2023-12-24,\n2023-12-25,\n2023-12-26,\n"
    partial_1 = "Date,\n2023-12-23,\n2023-12-24,\n2023-12-25,\n2023-12-26,\n"
    partial_2 = "Date,\n2023-12-22,\n2023-12-23,\n2023-12-24,\n"
    partial_3 = "Date,\n2023-12-20,\n2023-12-21,\n2023-12-22,\n2023-12-23,\n"
    empty = "Date,Open,High,Low,Close,Volume"

    def setUp(self) -> None:
        self.file = NamedTemporaryFile(mode="w+", suffix=".csv", delete=False)
        self.fname = Path(self.file.name)
        self.file.write(self.data)
        self.file.close()

        self.empty_file = NamedTemporaryFile(
            mode="w+", suffix=".csv", delete=False
        )
        self.emtpy_fname = Path(self.empty_file.name)
        self.empty_file.write(self.empty)
        self.empty_file.close()

    def tearDown(self) -> None:
        os.remove(self.fname)
        os.remove(self.emtpy_fname)

    def test_tiny_file(self):
        """Test returns entire data as DataFrame"""

        size = os.path.getsize(self.fname)

        df = csv_loader(self.fname, chunk_size=size + 10)

        expected_df = pd.read_csv(
            self.fname, index_col="Date", parse_dates=["Date"]
        )

        pd.testing.assert_frame_equal(df, expected_df)

    def test_large_file(self):
        """Expect test to return a partial data as DataFrame"""

        size = os.path.getsize(self.fname)

        df = csv_loader(self.fname, period=4, chunk_size=size // 2)

        expected_df = pd.read_csv(
            io.StringIO(self.partial_1),
            index_col="Date",
            parse_dates=["Date"],
        )

        pd.testing.assert_frame_equal(df, expected_df)

    def test_date_out_of_bounds(self):
        """Expect test to returns entire data as DataFrame"""

        size = os.path.getsize(self.fname)

        df = csv_loader(self.fname, chunk_size=size + 10)

        expected_df = pd.read_csv(
            self.fname, index_col="Date", parse_dates=["Date"]
        )

        pd.testing.assert_frame_equal(df, expected_df)

    def test_end_date(self):
        """Test returns partial data upto end date"""

        size = os.path.getsize(self.fname)

        df = csv_loader(
            self.fname,
            end_date=datetime(2023, 12, 24),
            period=3,
            chunk_size=size // 2,
        )

        expected_df = pd.read_csv(
            io.StringIO(self.partial_2), index_col="Date", parse_dates=["Date"]
        )

        pd.testing.assert_frame_equal(df, expected_df)

    def test_out_of_bounds_end_date(self):
        """Test raises IndexError"""

        with self.assertRaises(IndexError):
            csv_loader(
                self.fname,
                end_date=datetime(2023, 12, 15),
                period=3,
            )

    def test_end_date_with_out_of_bounds_start_date(self):
        """Test return data from start of file to end date"""

        size = os.path.getsize(self.fname)

        df = csv_loader(
            self.fname,
            end_date=datetime(2023, 12, 23),
            chunk_size=size // 2,
        )

        expected_df = pd.read_csv(
            io.StringIO(self.partial_3), index_col="Date", parse_dates=["Date"]
        )

        pd.testing.assert_frame_equal(df, expected_df)

    def test_end_date_with_empty_file(self):
        """Test raises a ValueError"""

        with self.assertRaises(ValueError):
            csv_loader(
                self.emtpy_fname,
                end_date=datetime(2024, 1, 18),
            )
