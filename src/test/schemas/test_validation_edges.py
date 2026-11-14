from datetime import date

import pytest
from pydantic import ValidationError

from src.app.schemas.alert import AlertUpdate
from src.app.schemas.financial import FinancialUpdate
from src.app.schemas.operation import OperationResponse, OperationUpdate
from src.app.schemas.passenger import PassengerUpdate
from src.app.schemas.preference import PreferenceUpdate
from src.app.schemas.report import ReportCreate
from src.app.schemas.user import UserUpdate


@pytest.mark.parametrize(
    "schema",
    [
        AlertUpdate,
        FinancialUpdate,
        OperationUpdate,
        PassengerUpdate,
        PreferenceUpdate,
        UserUpdate,
    ],
)
def test_partial_update_schemas_reject_empty_payload(schema):
    with pytest.raises(ValidationError, match="Informe ao menos um campo"):
        schema()


def test_operation_completion_rate_handles_zero_schedule():
    response = OperationResponse(
        id="op1",
        date=date(2026, 8, 1),
        scheduled_trips=0,
        completed_trips=0,
        created_at="2026-08-01T00:00:00Z",
        updated_at="2026-08-01T00:00:00Z",
    )

    assert response.completion_rate == 0


def test_report_period_rejects_end_before_start():
    with pytest.raises(ValidationError, match="data final"):
        ReportCreate(
            report_type="operations",
            format="csv",
            start_date=date(2026, 8, 31),
            end_date=date(2026, 8, 1),
        )
