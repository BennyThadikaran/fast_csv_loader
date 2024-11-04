import io
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


def csv_loader(
    file_path: Path,
    period: int = 160,
    end_date: Optional[datetime] = None,
    date_column: str = "Date",
    date_format: Optional[str] = None,
    chunk_size: int = 1024 * 6,
) -> pd.DataFrame:
    """
    Load a CSV file with timeseries data in chunks from the end.

    Could return an empty DataFrame, if no data was found.
    Use ``df.empty`` to check if the DataFrame is empty before further processing.

    :param file_path: The path to the CSV file to be loaded.
    :type file_path: pathlib.Path

    :param period: Number of lines/candles to return. The default is 160.
    :type period: int

    :param end_date: Load N lines up to this date.
        If None, will load the last N lines from the file.
        If the date is provided, load the last N lines from this date.
    :type end_date: Optional[datetime]

    :param date_column: Name of the date column. Defaults to ``Date``.
    :type date_column: str

    :param date_format: Custom date format in case pandas is unable to parse the date column.
    :type date_format: Optional[str]

    :param chunk_size: The size of data chunks loaded into memory.
        The default is 6144 bytes (6 KB).
    :type chunk_size: int

    :return: A DataFrame containing the loaded timeseries data.
    :rtype: pd.DataFrame

    :raise IndexError: if ``end_date`` is provided but not within the boundary of the data.
    """

    def get_date(start: int, chunk: bytes) -> datetime:
        """Helper function

        Parse the first occurence of a date string in a chunk at the
        given start index

        Raises a ValueError if date is invalid or not found
        """

        # Given the start point date column ends with ','
        end = chunk.find(b",", start)

        date_str = chunk[start:end].decode()

        # empty string returns NaT
        dt = pd.to_datetime(date_str)

        # Guard against NaT values
        if pd.isna(dt):
            raise ValueError("Not a Date")

        return dt

    size = os.path.getsize(file_path)

    if size <= max(1024 * 19, chunk_size):
        df = pd.read_csv(
            file_path,
            index_col=date_column,
            parse_dates=[date_column],
            date_format=date_format,
        )

        if end_date:
            dt = df.index[0]

            if isinstance(dt, pd.Timestamp) and dt.tzinfo:
                end_date = end_date.replace(tzinfo=dt.tzinfo)

            if not df.empty and end_date < dt:
                raise IndexError("Date out of bounds of current DataFrame")

            return df.loc[:end_date].iloc[-period:]

        return df.iloc[-period:]

    chunks_read = []  # store the bytes chunk in a list
    prev_chunk_start_line = None

    # Open in binary mode and read from end of file
    with file_path.open(mode="rb") as f:

        # Read the first line of file to get column names
        columns = f.readline()
        first_row_pos = f.tell()

        if end_date:
            dt = get_date(0, f.readline())

            if dt.tzinfo:
                end_date = end_date.replace(tzinfo=dt.tzinfo)

        curr_pos = size  # set current position to end of file
        lines_per_chunk = lines_read = 0

        while curr_pos >= first_row_pos:

            read_size = min(chunk_size, curr_pos - first_row_pos)

            if read_size == 0:
                break

            # Set the current read position in the file
            f.seek(curr_pos - read_size)

            # From the current position read n bytes
            chunk = f.read(read_size)

            # We're reading the first chunk
            if curr_pos == size:
                # Get an estimate of line count per chunk
                # We use this to keep track of lines read so far
                lines_per_chunk = chunk[:-1].count(b"\n") - 2

            # Get N lines upto end_date
            if end_date:

                # First line in a chunk may not be complete line
                # So skip the first line and parse the first date in chunk
                start = chunk.find(b"\n")

                try:
                    current_dt = get_date(start + 1, chunk)
                except ValueError:
                    chunks_read.append(chunk)
                    curr_pos -= read_size
                    continue

                # start storing chunks once end date has reached
                if current_dt <= end_date:

                    # Dont count the first chunk. If end_dt is near the start of
                    # the chunk, extra lines will be counted, resulting in fewer
                    # lines being returned than expected.
                    lines_read += 1 if lines_read == 0 else lines_per_chunk

                    if prev_chunk_start_line:
                        # As we append the first chunk, the last line of chunk
                        # may be incomplete. We keep a reference to the first
                        # line of the previous chunk and concat it here.
                        chunks_read.append(prev_chunk_start_line)
                        prev_chunk_start_line = None

                    # Count N periods from end_date
                    if lines_read >= period:
                        chunks_read.append(chunk[start + 1 :])
                        break

                    chunks_read.append(chunk)
                else:
                    # Keep a reference to the first line of chunk till we reach
                    # the current date
                    prev_chunk_start_line = chunk[:start]

            else:
                # Get N lines from end of file

                lines_read += lines_per_chunk

                if lines_read >= period:
                    start = chunk.find(b"\n") + 1
                    chunks_read.append(chunk[start:])
                    break

                # we are storing the chunks in bottom first order.
                # This has to be corrected later by reversing the list
                chunks_read.append(chunk)

            curr_pos -= read_size

        if end_date and not chunks_read:
            # If chunks_read is empty, end_date was not found in file
            raise IndexError("Date out of bounds of current DataFrame")

        # Reverse the list and join it into a bytes string.
        # Store the result in a buffer
        chunks_read.append(columns)
        buffer = io.BytesIO(b"".join(chunks_read[::-1]))

    df = pd.read_csv(
        buffer,
        parse_dates=[date_column],
        index_col=date_column,
        date_format=date_format,
    )

    if end_date:
        return df.loc[df.index <= end_date].iloc[-period:]
    else:
        return df.iloc[-period:]
