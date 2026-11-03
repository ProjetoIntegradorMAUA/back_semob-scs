from datetime import date

from src.app.schemas.common import ApiSchema


class TripTotals(ApiSchema):
    scheduled: int
    completed: int
    missing: int
    completion_rate: float


class OperationTotals(TripTotals):
    productive_km: float
    deadhead_km: float
    total_km: float


class DailyOperation(OperationTotals):
    date: date


class LineOperation(ApiSchema):
    line_code: str
    completed_trips: int
    total_km: float


class TimeBand(TripTotals):
    key: str
    label: str


class OperationAnalytics(ApiSchema):
    start_date: date
    end_date: date
    totals: OperationTotals
    daily: list[DailyOperation]
    lines: list[LineOperation]
    time_bands: list[TimeBand]


class PassengerTotals(ApiSchema):
    total: int
    paying: int
    fare_gate: int
    prepaid: int
    non_paying: int
    daily_average: float


class DailyPassengers(ApiSchema):
    date: date
    fare_gate: int
    prepaid: int
    non_paying: int
    paying: int
    total: int


class WeeklyPassengers(ApiSchema):
    week: int
    start_date: date
    end_date: date
    total: int
    daily_average: float
    change_percentage: float | None


class HourlySupply(ApiSchema):
    hour: int
    label: str
    vehicles: int
    trips: int


class PassengerAnalytics(ApiSchema):
    start_date: date
    end_date: date
    totals: PassengerTotals
    daily: list[DailyPassengers]
    weekly: list[WeeklyPassengers]
    hourly_supply: list[HourlySupply]


class FinancialTotals(ApiSchema):
    sales: float
    usage: float
    circulating_credit: float
    usage_rate: float
    daily_average_sales: float


class DailyFinancial(ApiSchema):
    date: date
    sales: float
    usage: float
    circulating_credit: float


class WeeklyFinancial(ApiSchema):
    week: int
    start_date: date
    end_date: date
    sales: float
    usage: float
    passengers: int


class MonthlyFinancial(ApiSchema):
    year: int
    month: int
    label: str
    sales: float
    usage: float
    circulating_credit: float


class FinancialAnalytics(ApiSchema):
    start_date: date
    end_date: date
    totals: FinancialTotals
    daily: list[DailyFinancial]
    weekly: list[WeeklyFinancial]
    monthly: list[MonthlyFinancial]
