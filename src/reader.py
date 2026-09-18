import polars as pl
from pathlib import Path


def read_batches(input_path: Path, input_chunk_size: int = 50000):
    """
    Read the CSV lazily and yield batches of records.

    input_path:
        Path of the input CSV dataset.

    input_chunk_size:
        Number of rows to process in each batch.
        Default is 50,000.

    read_batches() is an iterator, so it can be used
    with a loop in main.py to process one batch at a time.
    """

    # Read the CSV lazily.
    #
    # We keep "amount" as String initially because the raw
    # dataset can contain invalid values such as text.
    # Pydantic validation can then check and convert the value.
    lazy_df = pl.scan_csv(input_path, schema_overrides={"amount": pl.String})

    # collect_batches() executes the lazy query in chunks
    # instead of collecting the complete dataset at once.
    #
    # "yield from" yields each batch produced by
    # collect_batches() to whoever is calling read_batches().
    yield from lazy_df.collect_batches(chunk_size = input_chunk_size)