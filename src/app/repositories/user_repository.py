from src.app.db.session import client


def create_user(dados: dict):
    colecao = client["semob-scs"]["users"]
    resultado = colecao.insert_one(dados)
    return str(resultado.inserted_id)
