from src.app.db.session import client

colecao = client["semob-scs"]["frota_por_hora"]


def create_frota_hora(dados: dict):
    if dados is None:
        return None
    resultado = colecao.insert_one(dados)
    if resultado is None:
        return None
    return str(resultado.inserted_id)
