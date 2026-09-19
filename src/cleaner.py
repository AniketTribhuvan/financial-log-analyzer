from pathlib import Path
import shutil


def clean_output_folder(output_dir: Path) -> None:
    """
    Remove previous analyzer outputs before starting a new run.

    The output folder contains:
        valid_batches/      -> Parquet files containing valid data
        invalid_batches/    -> Parquet files containing invalid data
        anomalies.parquet   -> Parquet file containing detected anomalies

    Before every new run, old outputs are removed so that results
    from the previous run don't get mixed with the new results.
    """

    # Paths for all the output files/folders
    valid_dir = output_dir / "valid_batches"
    invalid_dir = output_dir / "invalid_batches"
    anomaly_file = output_dir / "anomalies.parquet"

    # Remove previous valid batch files
    if valid_dir.exists():
        shutil.rmtree(valid_dir)

    # Remove previous invalid batch files
    if invalid_dir.exists():
        shutil.rmtree(invalid_dir)

    # Remove previous anomaly file
    if anomaly_file.exists():
        anomaly_file.unlink()

    # Create fresh directories for the new run
    valid_dir.mkdir(parents=True, exist_ok=True)
    invalid_dir.mkdir(parents=True, exist_ok=True)