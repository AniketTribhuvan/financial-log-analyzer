# Data

This directory contains the tools and input data used for testing the Financial Log Analyzer.

## Dataset Generator

`dataset_generator.py` is a Python script used to generate a large synthetic financial transaction dataset for testing the pipeline.

The generator was created with AI assistance and is used only to create synthetic test data. The generated dataset does not contain real financial information.

Example:

```text
data/
 README.md
 dataset_generator.py
 raw_transactions_1GB.csv    # generated locally
```

## Why Generate the Dataset?

The main purpose of this project is to test how the pipeline behaves when processing a large dataset without loading the complete CSV into memory.

The generator allows the project to create a dataset of approximately 1 GB for:

- Batch-processing tests
- Memory-usage testing
- Validation testing
- Parquet-writing tests
- Anomaly-detection testing
- Performance benchmarking

## Generated Dataset

The large CSV dataset is generated locally and is **not committed to GitHub**.

This keeps the repository small while still allowing anyone to reproduce the test dataset using `dataset_generator.py`.

Generated files such as:

```text
raw_transactions_1GB.csv
```

are ignored by Git.

## Input Format

The generated transactions contain fields such as:

- `transaction_id`
- `user_id`
- `timestamp`
- `amount`
- `currency`
- `transaction_type`

The generated data is synthetic and intended for development and testing only.

## Important

Do not place real financial or personally identifiable information in this directory.

Use synthetic or anonymized data when testing the project.