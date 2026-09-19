from pathlib import Path
import polars as pl
from src.anomaly_detector import detect_anomalies


def test_anomaly_detection(tmp_path: Path):
    # Temporary directories/files are created by pytest.
    valid_dir = tmp_path / "valid_batches"
    anomaly_file = tmp_path / "anomalies.parquet"

    valid_dir.mkdir()

    # The first three transactions represent normal historical behavior.
    # They have some variation so that historical standard deviation > 0.
    #
    # Historical values:
    # 90, 100, 110
    #
    # mean = 100
    # population std ≈ 8.16
    # threshold = 100 + (3 × 8.16) ≈ 124.49
    #
    # Therefore, 1000 is an anomaly.
    data = {
        "transaction_id": [
            "TX0000000001",
            "TX0000000002",
            "TX0000000003",
            "TX0000000004",
        ],
        "user_id": [
            "U1001",
            "U1001",
            "U1001",
            "U1001",
        ],
        "timestamp": [
            "2025-01-01T10:00:00",
            "2025-01-02T10:00:00",
            "2025-01-03T10:00:00",
            "2025-01-04T10:00:00",
        ],
        "amount": [
            90.0,
            100.0,
            110.0,
            1000.0,
        ],
        "currency": [
            "INR",
            "INR",
            "INR",
            "INR",
        ],
        "transaction_type": [
            "payment",
            "payment",
            "payment",
            "payment",
        ],
    }

    # Create the test DataFrame and convert timestamp strings into Polars Datetime values.
    df = pl.DataFrame(data).with_columns(
        pl.col("timestamp").str.to_datetime()
    )

    # The anomaly detector expects valid transactions to be stored as Parquet files inside valid_dir.
    df.write_parquet(valid_dir / "batch1_valid.parquet")

    # Run the anomaly detection pipeline.
    anomaly_count = detect_anomalies(
        valid_dir,
        anomaly_file,
    )

    # Exactly one transaction should be detected as anomalous.
    assert anomaly_count == 1

    # Read the generated anomaly file and verify that the correct
    # transaction was detected.
    anomalies = pl.read_parquet(anomaly_file)

    assert anomalies["transaction_id"].to_list() == [
        "TX0000000004"
    ]