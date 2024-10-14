import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from context import csv_loader


def generate_random_prices(
    start_date, end_date, freq="D", tz=None, index_col="Date"
):
    """
    Generate random prices for a given date range.
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq, tz=tz)

    prices = np.random.randint(10, 100, size=len(date_range))

    df = pd.DataFrame({index_col: date_range, "Price": prices})
    df[index_col] = pd.to_datetime(df[index_col])
    return df.set_index(index_col, drop=True)


class Test_csv_loader(unittest.TestCase):

    def setUp(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            self.fname = Path(f.name)

    def tearDown(self) -> None:
        self.fname.unlink()

    def test_tiny_file(self):
        """Test returns entire data as DataFrame"""

        expected = generate_random_prices("2023-01-01", "2023-01-31")
        expected.to_csv(self.fname)

        df = csv_loader(self.fname)

        pd.testing.assert_frame_equal(df, expected)

    def test_large_file(self):
        """Returns a DataFrame of length 160"""

        df = generate_random_prices("2020-01-01", "2023-12-30")
        df.to_csv(self.fname)

        df = csv_loader(self.fname, chunk_size=1024 * 2)
        self.assertEqual(len(df), 160)

    def test_intraday_data(self):
        """Returns a DataFrame of length 160"""

        df = generate_random_prices(
            "2023-01-01T00:00",
            "2023-01-15T12:00",
            freq="15min",
            tz="America/New_York",
        )

        df.to_csv(self.fname)

        df = csv_loader(self.fname, chunk_size=1024 * 2)
        self.assertEqual(len(df), 160)

    def test_empty_file(self):
        """Raises pandas.Errors.EmptyDataError"""

        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = Path(f.name)

        with self.assertRaises(pd.errors.EmptyDataError):
            csv_loader(fname)

        fname.unlink()

    def test_empty_file_with_column_header(self):
        """Returns an emtpy DataFrame"""

        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = Path(f.name)
            f.write(b"Date,Price\n")

        df = csv_loader(fname)
        self.assertTrue(df.empty)

        fname.unlink()

    def test_end_date(self):
        """Test returns partial data upto end date"""

        df = generate_random_prices("2020-01-01", "2023-12-31")
        df.to_csv(self.fname)

        expected = df.loc[:"2023-11-30"].iloc[-400:]

        df = csv_loader(
            self.fname,
            end_date=pd.to_datetime("2023-11-30"),
            period=400,
            chunk_size=1024 * 3,
        )

        pd.testing.assert_frame_equal(df, expected)

    def test_end_date_with_intraday_data(self):
        """Returns a DataFrame of length 160"""

        df = generate_random_prices(
            "2023-01-01T00:00",
            "2023-01-15T12:00",
            freq="15min",
            tz="America/New_York",
        )

        df.to_csv(self.fname)

        df = csv_loader(
            self.fname,
            chunk_size=1024 * 2,
            end_date=pd.to_datetime("2023-01-10T15:30"),
        )

        end_date = pd.to_datetime("2023-01-10T15:30").tz_localize(
            "America/New_York"
        )

        self.assertEqual(len(df), 160)
        self.assertEqual(df.index[-1], end_date)

    def test_end_date_with_tz_aware_dates(self):
        """Test returns partial data upto end date"""

        df = generate_random_prices(
            "2020-01-01", "2023-12-31", tz="America/New_York"
        )

        df.to_csv(self.fname)

        df = csv_loader(
            self.fname,
            end_date=pd.to_datetime("2023-11-30"),
        )

        end_date = pd.to_datetime("2023-11-30").tz_localize("America/New_York")

        self.assertEqual(df.index[-1], end_date)
        self.assertEqual(len(df), 160)

    def test_out_of_bounds_end_date_small_file(self):
        """Test raises IndexError"""

        df = generate_random_prices("2023-01-01", "2023-01-31")
        df.to_csv(self.fname)

        with self.assertRaises(IndexError):
            csv_loader(
                self.fname,
                period=20,
                end_date=pd.to_datetime("2022-12-28"),
            )

    def test_out_of_bounds_end_date_large_file(self):
        """Test raises IndexError"""

        df = generate_random_prices("2020-01-01", "2023-12-31")
        df.to_csv(self.fname)

        with self.assertRaises(IndexError):
            csv_loader(
                self.fname,
                period=20,
                end_date=pd.to_datetime("2019-12-28"),
            )

    def test_end_date_with_data_less_than_period(self):
        """Test return data from start of file to end date"""

        df = generate_random_prices("2023-01-01", "2023-01-31")
        df.to_csv(self.fname)

        expected = df.loc[:"2023-01-10"]

        df = csv_loader(
            self.fname,
            period=20,
            end_date=pd.to_datetime("2023-01-10"),
        )

        pd.testing.assert_frame_equal(df, expected)


if __name__ == "__main__":
    unittest.main()
