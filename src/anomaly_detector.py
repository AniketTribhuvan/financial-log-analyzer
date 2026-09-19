import polars as pl
from pathlib import Path


def detect_anomalies(valid_file: Path, anomaly_file: Path) -> int:
    """
    Detect anomalous transactions using a 7-day rolling
    mean and standard deviation.

    The historical values are calculated separately for each
    user and currency combination.
    """

    # Read the valid Parquet file lazily.
    #
    # Lazy reading means Polars does not immediately load
    # all the data into memory.
    lf = pl.scan_parquet(str(valid_file))

    # Build the complete lazy query plan.
    plan = (
        lf

        # Rolling operations need the transactions to be
        # ordered by user, currency and timestamp.
        .sort([
            "user_id",
            "currency",
            "timestamp"
        ])

        # Create a helper column.
        #
        # Every transaction gets the value 1.
        # Later, rolling_sum_by() can use this column
        # to count historical transactions.
        .with_columns(
            pl.lit(1).alias("transaction_count")
        )

        # Calculate historical rolling statistics.
        .with_columns(

            # Calculate the mean amount from the previous
            # 7 days for the same user and currency.
            #
            # closed="left" means the current transaction
            # is NOT included in its own historical window.
            pl.col("amount")
            .rolling_mean_by(
                "timestamp",
                window_size="7d",
                closed="left",
                min_samples=1,
            )
            .over("user_id", "currency")
            .alias("rolling_mean"),

            # Calculate the standard deviation of transaction
            # amounts from the previous 7 days.
            pl.col("amount")
            .rolling_std_by(
                "timestamp",
                window_size="7d",
                closed="left",
                min_samples=1,
                ddof=0,
            )
            .over("user_id", "currency")
            .alias("rolling_std"),

            # Count how many transactions happened during
            # the previous 7 days.
            #
            # transaction_count contains 1 for every row,
            # so rolling_sum_by() works like a rolling count.
            pl.col("transaction_count")
            .rolling_sum_by(
                "timestamp",
                window_size="7d",
                closed="left",
            )
            .over("user_id", "currency")
            .alias("historical_count"),
        )

        # Create the final anomaly flag.
        .with_columns(
            (
                # We need at least 3 previous transactions
                # before using the statistical anomaly rule.
                (pl.col("historical_count") >= 3)

                # Standard deviation must be greater than 0.
                # If it is 0, there is no variation in the
                # historical transaction amounts.
                & (pl.col("rolling_std") > 0)

                # Anomaly rule:
                #
                # current amount > historical mean
                #                     + 3 × historical std
                &
                (
                    pl.col("amount")
                    > (
                        pl.col("rolling_mean")
                        + 3 * pl.col("rolling_std")
                    )
                )
            ).alias("is_anomaly")
        )

        # Keep only rows that were marked as anomalies.
        .filter(
            pl.col("is_anomaly")
        )
    )

    # Execute the lazy query and directly write the
    # anomaly result to a Parquet file.
    #
    # sink_parquet() is useful here because we don't need
    # the complete anomaly DataFrame in memory.
    plan.sink_parquet(
        str(anomaly_file)
    )

    # Read the generated anomaly file lazily and count
    # the number of detected anomalies.
    anomaly_count = (
        pl.scan_parquet(
            str(anomaly_file)
        )
        .select(
            pl.len()
        )
        .collect()
        .item()
    )

    # Return the total number of detected anomalies.
    return anomaly_count