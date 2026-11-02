from datetime import date

from src.app.schemas.common import ApiSchema


class DashboardTotals(ApiSchema):
    passengers: int
    paying_passengers: int
    non_paying_passengers: int
    scheduled_trips: int
    completed_trips: int
    missing_trips: int
    total_km: float
    completion_rate: float
    sales: float
    usage: float
    circulating_credit: float
    open_alerts: int


class DailyDashboardPoint(ApiSchema):
    date: date
    passengers: int = 0
    scheduled_trips: int = 0
    completed_trips: int = 0
    total_km: float = 0
    sales: float = 0
    usage: float = 0


class LineRanking(ApiSchema):
    line_code: str
    completed_trips: int
    total_km: float


class DashboardOverview(ApiSchema):
    start_date: date
    end_date: date
    totals: DashboardTotals
    daily: list[DailyDashboardPoint]
    top_lines: list[LineRanking]
