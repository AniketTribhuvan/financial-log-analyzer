import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

OUTPUT_FILE = Path("raw_transactions.csv")

TARGET_SIZE_GB = 1
TARGET_SIZE_BYTES = TARGET_SIZE_GB * 1024**3

BATCH_SIZE = 50_000

NUM_USERS = 100_000

CURRENCIES = ["INR", "USD", "EUR"]

TRANSACTION_TYPES = [
    "payment",
    "withdrawal",
    "transfer",
    "refund",
]

START_DATE = datetime(2025, 1, 1)

random.seed(42)


# ============================================================
# Dataset categories
# ============================================================

# Users in this group receive many transactions.
# This gives the analyzer enough history for rolling statistics.
ACTIVE_USERS = 10_000

# Users in this group receive only a few transactions.
# This allows insufficient-history cases to be tested.
LOW_HISTORY_USERS = 5_000


# ============================================================
# CSV schema
# ============================================================

HEADERS = [
    "transaction_id",
    "user_id",
    "timestamp",
    "amount",
    "currency",
    "transaction_type",
]


# ============================================================
# User profiles
# ============================================================

def create_user_profiles():
    """
    Give users different normal spending behaviors.

    Different users have different average transaction amounts.
    This is important because anomaly detection is performed
    per user rather than globally.
    """

    profiles = {}

    for user_number in range(1, NUM_USERS + 1):

        user_id = f"U{user_number:06d}"

        # Different users have different spending levels.
        base_amount = random.uniform(100, 10_000)

        profiles[user_id] = {
            "base_amount": base_amount,
            "currency": random.choice(CURRENCIES),
        }

    return profiles


# ============================================================
# Generate normal timestamp
# ============================================================

def generate_normal_timestamp():
    """
    Generate a timestamp somewhere inside the dataset period.
    """

    seconds_in_year = 365 * 24 * 60 * 60

    return START_DATE + timedelta(
        seconds=random.randint(0, seconds_in_year)
    )


# ============================================================
# Generate normal amount
# ============================================================

def generate_normal_amount(base_amount):
    """
    Generate an amount around the user's normal spending level.
    """

    amount = random.gauss(
        base_amount,
        base_amount * 0.20
    )

    return round(max(amount, 1), 2)


# ============================================================
# Generate one valid transaction
# ============================================================

def generate_normal_transaction(
    transaction_number,
    user_id,
    profile
):
    """

    Generate a normal valid transaction.
    """

    transaction_id = f"TX{transaction_number:010d}"

    timestamp = generate_normal_timestamp()

    amount = generate_normal_amount(
        profile["base_amount"]
    )

    currency = profile["currency"]

    transaction_type = random.choice(
        TRANSACTION_TYPES
    )

    return [
        transaction_id,
        user_id,
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        amount,
        currency,
        transaction_type,
    ]


# ============================================================
# Generate deliberate anomaly
# ============================================================

def generate_anomaly_transaction(
    transaction_number,
    user_id,
    profile
):
    """
    Generate a transaction that is deliberately far away
    from the user's normal transaction amount.
    """

    transaction_id = f"TX{transaction_number:010d}"

    timestamp = generate_normal_timestamp()

    # Extremely larger than the user's normal behavior.
    amount = round(
        profile["base_amount"] * random.uniform(15, 40),
        2
    )

    return [
        transaction_id,
        user_id,
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        amount,
        profile["currency"],
        "payment",
    ]


# ============================================================
# Generate invalid transaction
# ============================================================

def generate_invalid_transaction(
    transaction_number,
    user_id,
    profile,
    invalid_type
):
    """
    Generate intentionally corrupted records.

    These records are used to test Pydantic validation.
    """

    transaction_id = f"TX{transaction_number:010d}"

    timestamp = generate_normal_timestamp()

    amount = generate_normal_amount(
        profile["base_amount"]
    )

    currency = profile["currency"]

    transaction_type = random.choice(
        TRANSACTION_TYPES
    )

    # --------------------------------------------------------
    # Invalid amount
    # --------------------------------------------------------

    if invalid_type == "non_numeric_amount":
        amount = "abc"

    elif invalid_type == "negative_amount":
        amount = -abs(amount)

    # --------------------------------------------------------
    # Invalid timestamp
    # --------------------------------------------------------

    elif invalid_type == "invalid_timestamp":
        timestamp = "INVALID_TIMESTAMP"

    # --------------------------------------------------------
    # Missing user ID
    # --------------------------------------------------------

    elif invalid_type == "missing_user":
        user_id = ""

    # --------------------------------------------------------
    # Invalid currency
    # --------------------------------------------------------

    elif invalid_type == "invalid_currency":
        currency = "XYZ"

    # --------------------------------------------------------
    # Missing transaction ID
    # --------------------------------------------------------

    elif invalid_type == "missing_transaction_id":
        transaction_id = ""

    # --------------------------------------------------------
    # Invalid transaction type
    # --------------------------------------------------------

    elif invalid_type == "invalid_transaction_type":
        transaction_type = "unknown"

    return [
        transaction_id,
        user_id,
        (
            timestamp.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(timestamp, datetime)
            else timestamp
        ),
        amount,
        currency,
        transaction_type,
    ]


# ============================================================
# Generate low-history user transaction
# ============================================================

def generate_low_history_transaction(
    transaction_number,
    user_id,
    profile
):
    """
    Generate transactions for users with very little history.

    These users allow the analyzer to test what happens when
    there isn't enough historical data for reliable statistics.
    """

    return generate_normal_transaction(
        transaction_number,
        user_id,
        profile
    )


# ============================================================
# Generate duplicate transaction ID
# ============================================================

def generate_duplicate_transaction(
    original_transaction
):
    """
    Return a copy of a transaction while preserving its
    transaction ID.

    This allows uniqueness validation to be tested.
    """

    return original_transaction.copy()


# ============================================================
# Dataset generation
# ============================================================

def generate_dataset():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    profiles = create_user_profiles()

    transaction_number = 1

    duplicate_source = None

    invalid_types = [
        "non_numeric_amount",
        "negative_amount",
        "invalid_timestamp",
        "missing_user",
        "invalid_currency",
        "missing_transaction_id",
        "invalid_transaction_type",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(HEADERS)

        while file.tell() < TARGET_SIZE_BYTES:

            rows = []

            for _ in range(BATCH_SIZE):

                # ==================================================
                # Decide what kind of record to generate
                # ==================================================

                probability = random.random()

                # --------------------------------------------------
                # 0.6% invalid records
                # --------------------------------------------------

                if probability < 0.006:

                    user_number = random.randint(
                        1,
                        NUM_USERS
                    )

                    user_id = f"U{user_number:06d}"

                    profile = profiles[user_id]

                    invalid_type = random.choice(
                        invalid_types
                    )

                    row = generate_invalid_transaction(
                        transaction_number,
                        user_id,
                        profile,
                        invalid_type
                    )

                # --------------------------------------------------
                # 0.3% deliberate anomalies
                # --------------------------------------------------

                elif probability < 0.009:

                    user_number = random.randint(
                        1,
                        ACTIVE_USERS
                    )

                    user_id = f"U{user_number:06d}"

                    profile = profiles[user_id]

                    row = generate_anomaly_transaction(
                        transaction_number,
                        user_id,
                        profile
                    )

                # --------------------------------------------------
                # Normal transaction
                # --------------------------------------------------

                else:

                    # Most transactions belong to active users.
                    if random.random() < 0.90:

                        user_number = random.randint(
                            1,
                            ACTIVE_USERS
                        )

                    else:

                        user_number = random.randint(
                            ACTIVE_USERS + 1,
                            NUM_USERS
                        )

                    user_id = f"U{user_number:06d}"

                    profile = profiles[user_id]

                    row = generate_normal_transaction(
                        transaction_number,
                        user_id,
                        profile
                    )

                rows.append(row)

                # Keep one transaction available for
                # duplicate-ID testing.
                if (
                    duplicate_source is None
                    and transaction_number > 10_000
                ):
                    duplicate_source = row.copy()

                transaction_number += 1

            # ==================================================
            # Occasionally insert a duplicate transaction ID
            # ==================================================

            if (
                duplicate_source is not None
                and random.random() < 0.01
            ):
                rows.append(
                    generate_duplicate_transaction(
                        duplicate_source
                    )
                )

            writer.writerows(rows)

            current_size = file.tell()

            print(
                f"Generated: "
                f"{current_size / (1024**2):,.2f} MB | "
                f"Transactions: "
                f"{transaction_number - 1:,}"
            )

    final_size = OUTPUT_FILE.stat().st_size

    print("\n========================================")
    print("Dataset generation complete")
    print("========================================")

    print(f"File: {OUTPUT_FILE}")

    print(
        f"Final size: "
        f"{final_size / (1024**3):.2f} GB"
    )

    print(
        f"Total transactions: "
        f"{transaction_number - 1:,}"
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    generate_dataset()