from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from src.app.schemas.operation import OperationResponse, OperationUpdate
from src.app.schemas.passenger import PassengerResponse
from src.app.schemas.report import ReportCreate


def test_operation_response_computes_indicators():
    now = datetime.now(timezone.utc)
    operation = OperationResponse(
        id="66f000000000000000000001",
        date=date(2026, 8, 1),
        scheduled_trips=100,
        completed_trips=98,
        productive_km=700.5,
        deadhead_km=20.25,
        created_at=now,
        updated_at=now,
    )

    assert operation.missing_trips == 2
    assert operation.total_km == 720.75
    assert operation.completion_rate == 98


def test_passenger_response_computes_totals():
    now = datetime.now(timezone.utc)
    passengers = PassengerResponse(
        id="66f000000000000000000001",
        date=date(2026, 8, 1),
        fare_gate=10,
        prepaid=4,
        non_paying=20,
        created_at=now,
        updated_at=now,
    )

    assert passengers.paying == 14
    assert passengers.total == 34


def test_empty_update_is_rejected():
    with pytest.raises(ValidationError):
        OperationUpdate()


def test_report_period_must_be_ordered():
    with pytest.raises(ValidationError):
        ReportCreate(
            report_type="operacional",
            format="pdf",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 8, 1),
        )
