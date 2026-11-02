from src.app.services.smart_report_parser import (
    parse_financials,
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
