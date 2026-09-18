import datetime
from pydantic import BaseModel, ValidationError, field_validator


# Currencies supported by the dataset
SUPPORTED_CURRENCIES = ["USD", "INR", "EUR"]


# Transaction types supported by the dataset
SUPPORTED_TRANSACTION_TYPES = ["transfer", "payment", "withdrawal", "refund"]


class Transaction(BaseModel):
    """
    Pydantic model representing one transaction record.

    Type annotations handle the basic type validation,
    while the custom validators below check the dataset-specific rules.
    """

    transaction_id: str
    user_id: str
    timestamp: datetime.datetime
    amount: float
    currency: str
    transaction_type: str

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: str):
        """
        Check whether transaction_id follows the required format.

        Expected format:
            TX + 10 digits

        Example:
            TX1234567890
        """

        if (
            value == ""
            or value[:2] != "TX"
            or len(value) != 12
            or not value[2:].isdigit()
        ):
            raise ValueError("transaction_id shouldn't be empty & must have specified format.")

        return value

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str):
        """
        Check whether user_id follows the required format.

        Expected format:
            U + one or more digits

        Example:
            U123
        """

        if (
            value == ""
            or value[:1] != "U"
            or not value[1:].isdigit()
        ):
            raise ValueError("user_id shouldn't be empty & must have specified format.")

        return value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime.datetime):
        """
        Check whether timestamp is within the dataset's date range.

        Valid range:
            2025-01-01 (inclusive)
            to
            2026-01-01 (exclusive)
        """

        if (
            value < datetime.datetime(2025, 1, 1)
            or value >= datetime.datetime(2026, 1, 1)
        ):
            raise ValueError("Datetime should be in dataset's range.")

        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value):
        """
        Transaction amount must be greater than 0.
        """

        if value <= 0:
            raise ValueError("amount should be greater than 0.")

        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value):
        """
        Check whether the currency is supported by the dataset.
        """

        if (
            value == ""
            or value not in SUPPORTED_CURRENCIES
        ):
            raise ValueError("Dataset doesn't support the currency.")

        return value

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, value):
        """
        Check whether the transaction type is supported.
        """

        if (
            value == ""
            or value not in SUPPORTED_TRANSACTION_TYPES
        ):
            raise ValueError("Dataset doesn't support transaction_type.")

        return value


def validate_batch(
    batch,
    seen_transaction_ids: set,
):
    """
    Validate one batch and separate valid and invalid records.

    seen_transaction_ids stores transaction IDs that were already
    accepted from previous batches.

    This is important because duplicate transaction IDs can exist
    across different batches, not only inside the current batch.
    """

    # Lists used to store the results of the current batch
    valid_batch = []
    invalid_batch = []

    # Counters for this batch
    valid_rows = 0
    invalid_rows = 0
    total_records = 0

    # Process one record at a time
    for row_dict in batch.iter_rows(named=True):

        total_records += 1

        try:
            # Create a Pydantic Transaction object.
            #
            # Pydantic first performs type validation/conversion
            # and then runs the custom field validators.
            row = Transaction(**row_dict)

        except ValidationError as err:

            # This record failed validation
            invalid_rows += 1

            # A single record can have multiple validation errors.
            # Store each error separately so we know exactly
            # which field caused the problem.
            for error in err.errors():

                invalid_batch.append(
                    {
                        "transaction_id": row_dict["transaction_id"],
                        "amount": row_dict["amount"],
                        "error_field": ".".join(
                            str(x) for x in error["loc"]
                        ),
                        "error_type": error["type"],
                        "error_message": error["msg"],
                    }
                )

        else:

            # Pydantic validation passed.
            # Now check for duplicate transaction_id.
            if row.transaction_id in seen_transaction_ids:

                # Duplicate transaction IDs are invalid.
                invalid_batch.append(
                    {
                        "transaction_id": row_dict["transaction_id"],
                        "amount": row_dict["amount"],
                        "error_field": "transaction_id",
                        "error_type": "DUPLICATE_TRANSACTION_ID",
                        "error_message": "transaction_id must be unique.",
                    }
                )

                invalid_rows += 1

            else:

                # This is a valid and unique transaction.
                #
                # Add its ID to the set so that the same ID
                # cannot be accepted later from another batch.
                seen_transaction_ids.add(row.transaction_id)

                valid_rows += 1

                # Convert the Pydantic model back into a dictionary.
                # This dictionary can later be converted into
                # a Polars DataFrame and written to Parquet.
                valid_batch.append(row.model_dump())

    # Return all results and counters for this batch.
    return (
        valid_batch,
        invalid_batch,
        valid_rows,
        invalid_rows,
        total_records,
    )