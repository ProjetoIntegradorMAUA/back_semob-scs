from fastapi.testclient import TestClient

from src.app.main import app, get_rota_teste


def test_rota_teste_legacy():
    assert get_rota_teste() == {"mensagem": "Teste Funcionando"}


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "SEMOB-SCS API"
