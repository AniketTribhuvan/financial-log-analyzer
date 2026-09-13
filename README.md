# Financial Log Analyzer

A memory-aware financial transaction processing pipeline built with **Python, Polars, and Pydantic**.

The project processes large transaction logs in batches, validates and cleans the data, detects duplicate transactions, stores the results in Parquet, and performs statistical anomaly detection on transaction history.

> Built to learn how a real data-processing pipeline handles large datasets instead of simply loading everything into RAM.

---

## What I Built

```text
Raw CSV
   ↓
Batch Processing (50,000 rows)
   ↓
Pydantic Validation
   ↓
Duplicate Detection
   ↓
Valid / Invalid Parquet
   ↓
Single Valid Parquet Dataset
   ↓
Lazy Polars Analysis
   ↓
7-Day Rolling Statistics
   ↓
Anomaly Detection (Three-Sigma Rule)
```

### Key Features

- Processes CSV data in **50,000-row batches** instead of loading the complete dataset at once.
- Uses **Pydantic** for schema validation and custom business rules.
- Detects duplicate `transaction_id` values across batches.
- Stores invalid records and validation errors in batch-wise Parquet files.
- Consolidates all valid batches into a single `valid_transactions.parquet` file.
- Uses **Polars LazyFrame** for downstream analytical processing.
- Calculates 7-day rolling statistics separately for each `user_id + currency`.
- Excludes the current transaction from its historical baseline.
- Flags unusually large transactions using a `mean + 3σ` threshold.
- Cleans previous generated outputs before every run.

---

## Tech Stack

**Python · Polars · Pydantic · psutil · pytest**

Main concepts:

`Batch Processing` · `Lazy Execution` · `Data Validation` · `Time-based Rolling Windows` · `Statistical Anomaly Detection` · `Memory Monitoring`

---

## Project Structure

```text
financial-log-analyzer/
  data/
    dataset_generator.py                       # Generates large synthetic transaction datasets for testing
    README.md                                  # Data directory overview and dataset-generation instructions

  output/
    README.md                                  # Explains generated validation and anomaly-detection outputs

  src/
    anomaly_detector.py                        # Detects anomalies using 7-day rolling mean and standard deviation
    cleaner.py                                 # Removes previous generated outputs and recreates output directories
    main.py                                    # Orchestrates the complete transaction-processing pipeline
    reader.py                                  # Lazily reads the raw CSV and processes it in batches
    validator.py                               # Pydantic validation and duplicate transaction detection

  tests/
    test_anomaly_detector.py                   # Tests statistical anomaly detection
    test_validator.py                          # Tests transaction validation rules

  .gitignore                                   # Excludes datasets, generated outputs, caches, and environment files
  README.md                                    # Project overview, architecture, features, and usage
  requirements.txt                              # Python dependencies
```

The code is split into modules based on responsibility:

- `reader.py` → batch reading
- `validator.py` → Pydantic validation + duplicate detection
- `cleaner.py` → output cleanup
- `anomaly_detector.py` → Polars analytical pipeline
- `main.py` → pipeline orchestration

---

## Anomaly Detection

For every transaction, the system looks at transactions from the **same user and currency during the previous 7 days**.

A transaction is flagged when:

\[
amount > rolling\_mean + 3 \times rolling\_std
\]

Additional conditions:

```text
historical_count >= 3
rolling_std > 0
```

The current transaction is excluded from its own historical window using:

```python
closed="left"
```

Separating by currency is important because comparing values such as `₹10,000` and `$10,000` directly would not be meaningful.

---

## Why Polars + Parquet?

I wanted the project to work with larger datasets without relying on:

```python
df = pl.read_csv(...)
```

for the entire raw file.

Instead:

```text
Large CSV
   ↓
small batches
   ↓
validation
   ↓
batch Parquet files
   ↓
single valid Parquet file
   ↓
lazy analytical queries
```

Each batch is validated independently and written to Parquet. After processing, the valid batch files are consolidated into:

```text
output/valid_transactions.parquet
```

The individual valid batch files are then removed.

The final valid Parquet file is read lazily by the anomaly detector, so the complete dataset does not need to be loaded into a Python DataFrame before analysis.

This also separates the **data-cleaning stage** from the **analysis stage**, which makes the pipeline easier to extend.

---

## Memory Monitoring

The pipeline also monitors the Python process memory usage while processing the dataset.

It uses **psutil** to measure the process's RSS memory and tracks the highest observed value during processing.

This helps evaluate how the pipeline behaves when processing a large dataset without loading the entire CSV into memory.

In one benchmark using approximately **17.2 million records** from a roughly **1 GB CSV**, the pipeline reached about **4.7 GB peak process memory**.

A major memory cost came from the Python/Pydantic validation layer and the `seen_transaction_ids` set used for duplicate detection.

When duplicate-ID tracking was removed during testing, peak memory dropped from roughly **4.7 GB to 3.4 GB**, showing that batch processing alone does not guarantee low memory usage.

The goal of this project is therefore **memory-aware processing** rather than claiming extremely low memory usage.

The monitoring is intended for **benchmarking and learning**, not production-grade performance monitoring.

---

## Testing

The project uses **pytest** for automated testing.

The tests cover:

- Transaction validation rules
- Invalid transaction handling
- Duplicate transaction detection
- Statistical anomaly detection
- Historical rolling-window behavior

---

## What I Learned

This project helped me understand:

- How batch processing reduces memory pressure.
- How Polars lazy execution works.
- How Pydantic can be used as a data-validation layer.
- How to handle validation errors without stopping the entire pipeline.
- Why duplicate detection requires state across batches.
- Why Parquet is useful for analytical workloads.
- How batch Parquet files can be consolidated into a single analytical dataset.
- How time-based rolling windows work.
- How to build a simple statistical anomaly detector.
- How to monitor process memory during large-data processing.
- How to break a data pipeline into maintainable Python modules.

---

## Current Limitations

This is a learning/portfolio project, not a production fraud-detection system.

Current limitations include:

- Duplicate IDs are tracked in a Python `set`, which grows with the number of unique transactions.
- The anomaly detector uses a simple statistical baseline rather than a machine-learning model.
- Currency values are analyzed separately rather than converted using historical FX rates.
- The current pipeline is designed for batch processing rather than a true event-streaming system.
- Pydantic validation creates Python objects, which can increase memory usage for large batches.

---

## Future Improvements

- Improve large-scale duplicate detection to reduce persistent memory usage.
- Add structured logging and configuration.
- Compare `mean + 3σ` with robust methods such as **Median + MAD**.
- Experiment with ML-based anomaly detection.
- Explore more scalable processing and storage strategies for larger datasets.

---

### Run the Tests

First, open a terminal and move to the project root:

```bash
cd "D:\Repos\Financial Log Analyzer"
```

Then run:

```bash
python -m pytest
```

To see more detailed test output:

```bash
python -m pytest -v
```

To run only the validator tests:

```bash
python -m pytest tests/test_validator.py
```

To run only the anomaly detection tests:

```bash
python -m pytest tests/test_anomaly_detector.py
```

Running pytest from the **project root directory** is important because the tests import modules from the `src` package.

---

## Running the Project

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd financial-log-analyzer
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate the Dataset

The project does not include the large raw CSV dataset.

Generate it locally using:

```bash
python data/dataset_generator.py
```

The generated dataset will be used as the input for the pipeline.

### 5. Run the Pipeline

```bash
python src/main.py
```

The pipeline will:

1. Read the CSV in batches.
2. Validate each transaction.
3. Detect duplicate transaction IDs.
4. Write valid and invalid records to batch Parquet files.
5. Consolidate the valid records into `valid_transactions.parquet`.
6. Remove the individual valid batch files.
7. Run lazy statistical anomaly detection.
8. Write detected anomalies to `anomalies.parquet`.
9. Display processing and memory statistics.

---

## Status

**Working prototype — actively improving**

The main pipeline is complete. Future work will focus on scalability, better duplicate detection, and comparing different anomaly-detection methods.

---

## Author

**Aniket**

AI/ML Diploma Student · Building projects to understand AI/ML and data engineering from the ground up.