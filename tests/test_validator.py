import datetime
import pytest
from pydantic import ValidationError
from src.validator import Transaction


def valid_transaction():
    return {
        "transaction_id": "TX0000000001",
        "user_id": "U1001",
        "timestamp": datetime.datetime(2025, 1, 10, 12, 30),
        "amount": 2500.0,
        "currency": "INR",
        "transaction_type": "payment",
    }


def test_valid_transaction():
    transaction = Transaction(**valid_transaction())

    assert transaction.transaction_id == "TX0000000001"
    assert transaction.user_id == "U1001"
    assert transaction.amount == 2500.0


def test_invalid_transaction_id():
    data = valid_transaction()
    data["transaction_id"] = "INVALID"

    with pytest.raises(ValidationError):
        Transaction(**data)


def test_invalid_user_id():
    data = valid_transaction()
    data["user_id"] = "INVALID"

    with pytest.raises(ValidationError):
        Transaction(**data)


def test_invalid_timestamp():
    data = valid_transaction()
    data["timestamp"] = datetime.datetime(2026, 1, 1)

    with pytest.raises(ValidationError):
        Transaction(**data)


def test_invalid_amount():
    data = valid_transaction()
    data["amount"] = -100

    with pytest.raises(ValidationError):
        Transaction(**data)


def test_invalid_currency():
    data = valid_transaction()
    data["currency"] = "GBP"

    with pytest.raises(ValidationError):
        Transaction(**data)


def test_invalid_transaction_type():
    data = valid_transaction()
    data["transaction_type"] = "unknown"

    with pytest.raises(ValidationError):
        Transaction(**data)