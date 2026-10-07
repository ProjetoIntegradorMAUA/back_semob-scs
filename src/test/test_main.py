from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_rota_teste():
    resposta = client.get("/teste")
    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Teste Funcionando"}
