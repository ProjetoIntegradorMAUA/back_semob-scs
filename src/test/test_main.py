from src.app.main import get_rota_teste


def test_rota_teste():
    assert get_rota_teste() == {"mensagem": "Teste Funcionando"}
