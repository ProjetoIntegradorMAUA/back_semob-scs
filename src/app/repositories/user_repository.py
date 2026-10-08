from src.app.db.session import client

colecao = client["semob-scs"]["users"]


def create_user(dados: dict):
    resultado = colecao.insert_one(dados)
    return str(resultado.inserted_id)


def get_users():
    resultado = colecao.find({}, {"nome": 1, "email": 1})
    return [
        {
            "id": str(user["_id"]),
            "nome": user["nome"],
            "email": user["email"]
        }
        for user in resultado
    ]
