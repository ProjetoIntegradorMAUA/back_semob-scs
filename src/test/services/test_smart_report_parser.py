from src.app.services.smart_report_parser import (
    parse_financials,
    parse_hourly_operations,
    parse_operation_fcv,
    parse_operation_lines,
    parse_operations,
    parse_passengers,
)


def test_parse_operations_with_brazilian_decimals():
    content = b"""
    <table><th>Data</th><th>diaSem</th><th>nrVeiculos</th><th>nrMaxVeicFx</th>
    <th>nrViagensProgr</th><th>nrViagensRealiz</th><th>kmProd</th><th>kmImprod</th>
    <tr><td>01/08/2026</td><td>Sab</td><td>37</td><td>35</td><td>924</td>
    <td>920</td><td>6889,4</td><td>344,3</td></tr></table>
    """
    rows = parse_operations(content)

    assert len(rows) == 1
    assert rows[0]["completed_trips"] == 920
    assert rows[0]["productive_km"] == 6889.4


def test_parse_passengers_ignores_total_row():
    content = """
    <table><th>Mês</th><th>Dia</th><th>Catraca</th><th>Antecipados</th>
    <th>Não Pagantes</th><th>Total Passageiros</th>
    <tr><td>2026-08</td><td>01</td><td>5.168</td><td>676</td><td>10.700</td><td>16.544</td></tr>
    <tr><td>2026-08</td><td>Total Mês</td><td>5.168</td><td>676</td><td>10.700</td><td>16.544</td></tr>
    </table>
    """.encode("utf-8")
    rows = parse_passengers(content)

    assert len(rows) == 1
    assert rows[0]["fare_gate"] == 5168
    assert rows[0]["non_paying"] == 10700


def test_parse_financials_merges_tables_by_date():
    content = """
    <table><th>Mês</th><th>Dia</th><th>Série</th><th>Créditos transferidos para cartões</th><th>Saldo Final</th>
    <tr><td>2026-08</td><td>01</td><td>1</td><td>1.234,50</td><td>20.000,00</td></tr></table>
    <table><th>Mês</th><th>Dia</th><th>Total Vendas</th><th>Total Utilização</th><th>Crédito Circulante</th>
    <tr><td>2026-08</td><td>01</td><td>2.000,00</td><td>1.500,00</td><td>500,00</td></tr></table>
    """.encode("utf-8")
    rows = parse_financials(content)

    assert len(rows) == 1
    assert rows[0]["sales"] == 2000
    assert rows[0]["credits_transferred"] == 1234.5


def test_parse_operation_lines_and_fcv():
    lines = b"""
    <table><tr><th>Data</th><th>Linha</th><th>kmTotal</th><th>nrViagens</th></tr>
    <tr><td>01/08/2026</td><td>03</td><td>1.234,5</td><td>120</td></tr></table>
    """
    fcv = b"""
    <table><tr><th>Data</th><th>Manha P</th><th>Manha R</th><th>Tarde P</th>
    <th>Tarde R</th><th>Noite P</th><th>Noite R</th><th>Programadas</th><th>Realizadas</th></tr>
    <tr><td>01/08/2026</td><td>40</td><td>39</td><td>35</td><td>34</td>
    <td>25</td><td>24</td><td>100</td><td>97</td></tr></table>
    """

    line_rows = parse_operation_lines(lines)
    fcv_rows = parse_operation_fcv(fcv)

    assert line_rows[0]["line_code"] == "03"
    assert line_rows[0]["productive_km"] == 1234.5
    assert fcv_rows[0]["scheduled_trips"] == 100
    assert fcv_rows[0]["night_completed"] == 24


def test_parse_hourly_operations_consolidated_and_by_line():
    summary = b"""
    <table><tr><th>Data</th><th>Fx Hor</th><th>nrVeiculos</th><th>nrViagens</th></tr>
    <tr><td>01/08/2026</td><td>4hs</td><td>11</td><td>14</td></tr></table>
    """
    detail = b"""
    <table><tr><th>Data</th><th>Linha</th><th>Fx Hor</th><th>nrVeiculos</th><th>nrViagens</th></tr>
    <tr><td>01/08/2026</td><td>01</td><td>23hs</td><td>2</td><td>3</td></tr></table>
    """

    summary_rows = parse_hourly_operations(summary)
    detail_rows = parse_hourly_operations(detail)

    assert summary_rows[0]["hour"] == 4
    assert summary_rows[0]["line_code"] is None
    assert detail_rows[0]["hour"] == 23
    assert detail_rows[0]["line_code"] == "01"


def test_parse_hourly_operations_rejects_invalid_hour():
    content = b"""
    <table><tr><th>Data</th><th>Fx Hor</th><th>nrVeiculos</th><th>nrViagens</th></tr>
    <tr><td>01/08/2026</td><td>invalida</td><td>1</td><td>1</td></tr></table>
    """

    assert parse_hourly_operations(content) == []
