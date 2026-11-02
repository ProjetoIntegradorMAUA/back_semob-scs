from datetime import datetime
from html.parser import HTMLParser
import re
import unicodedata
from typing import Callable

from src.app.models.common import DataSource


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def _finish_row(self) -> None:
        if self._table is not None and self._row:
            self._table.append(self._row)
        self._row = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._finish_row()
            self._row = []
        elif tag in {"th", "td"} and self._table is not None:
            if self._row is None:
                self._row = []
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self._cell is not None:
            assert self._row is not None
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr":
            self._finish_row()
        elif tag == "table" and self._table is not None:
            self._finish_row()
            if self._table:
                self.tables.append(self._table)
            self._table = None


def _text(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("cp1252", errors="replace")


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _number(value: str) -> float:
    cleaned = value.replace("\xa0", " ").strip().replace(" ", "")
    cleaned = cleaned.replace(".", "").replace(",", ".")
    return float(cleaned or 0)


def _integer(value: str) -> int:
    return int(round(_number(value)))


def _date_br(value: str):
    return datetime.strptime(value.strip(), "%d/%m/%Y").date()


def _month_day(month: str, day: str):
    return datetime.strptime(f"{month.strip()}-{day.strip()}", "%Y-%m-%d").date()


def _tables(content: bytes) -> list[tuple[list[str], list[list[str]]]]:
    parser = _TableParser()
    parser.feed(_text(content))
    result = []
    for table in parser.tables:
        if len(table) < 2:
            continue
        width = len(table[0])
        if width and all(len(row) == width for row in table[1:]):
            result.append(([_normalize(value) for value in table[0]], table[1:]))
    return result


def _matching_table(content: bytes, required: set[str]):
    for headers, rows in _tables(content):
        if required.issubset(set(headers)):
            return headers, rows
    expected = ", ".join(sorted(required))
    raise ValueError(f"Tabela esperada não encontrada. Colunas requeridas: {expected}.")


def parse_operations(content: bytes) -> list[dict]:
    headers, rows = _matching_table(content, {"data", "nrviagensprogr", "nrviagensrealiz"})
    index = {name: position for position, name in enumerate(headers)}
    parsed = []
    for row in rows:
        try:
            day = _date_br(row[index["data"]])
        except (ValueError, IndexError):
            continue
        parsed.append(
            {
                "date": day,
                "line_code": None,
                "vehicles_operated": _integer(row[index["nrveiculos"]]),
                "max_vehicles_in_service": _integer(row[index["nrmaxveicfx"]]),
                "scheduled_trips": _integer(row[index["nrviagensprogr"]]),
                "completed_trips": _integer(row[index["nrviagensrealiz"]]),
                "productive_km": _number(row[index["kmprod"]]),
                "deadhead_km": _number(row[index["kmimprod"]]),
                "source": DataSource.SMART_REPORT.value,
            }
        )
    return parsed


def parse_passengers(content: bytes) -> list[dict]:
    headers, rows = _matching_table(content, {"mes", "dia", "catraca", "naopagantes"})
    index = {name: position for position, name in enumerate(headers)}
    parsed = []
    for row in rows:
        if not row[index["dia"]].isdigit():
            continue
        parsed.append(
            {
                "date": _month_day(row[index["mes"]], row[index["dia"]]),
                "fare_gate": _integer(row[index["catraca"]]),
                "prepaid": _integer(row[index["antecipados"]]),
                "non_paying": _integer(row[index["naopagantes"]]),
                "source": DataSource.SMART_REPORT.value,
            }
        )
    return parsed


def parse_financials(content: bytes) -> list[dict]:
    by_date: dict = {}
    for headers, rows in _tables(content):
        columns = set(headers)
        index = {name: position for position, name in enumerate(headers)}
        if {"mes", "dia", "totalvendas", "totalutilizacao"}.issubset(columns):
            for row in rows:
                if not row[index["dia"]].isdigit():
                    continue
                day = _month_day(row[index["mes"]], row[index["dia"]])
                item = by_date.setdefault(day, {"date": day})
                item.update(
                    sales=_number(row[index["totalvendas"]]),
                    usage=_number(row[index["totalutilizacao"]]),
                )
        elif {"mes", "dia", "creditostransferidosparacartoes", "saldofinal"}.issubset(columns):
            for row in rows:
                if not row[index["dia"]].isdigit():
                    continue
                day = _month_day(row[index["mes"]], row[index["dia"]])
                item = by_date.setdefault(day, {"date": day})
                item.update(
                    credits_transferred=_number(row[index["creditostransferidosparacartoes"]]),
                    system_balance=_number(row[index["saldofinal"]]),
                )
    if not by_date:
        raise ValueError("Nenhuma tabela financeira reconhecida no arquivo.")
    return [
        {
            "sales": 0.0,
            "usage": 0.0,
            "credits_transferred": 0.0,
            "system_balance": None,
            "source": DataSource.SMART_REPORT.value,
            **item,
        }
        for _, item in sorted(by_date.items())
    ]


PARSERS: dict[str, Callable[[bytes], list[dict]]] = {
    "operations": parse_operations,
    "passengers": parse_passengers,
    "financials": parse_financials,
}
