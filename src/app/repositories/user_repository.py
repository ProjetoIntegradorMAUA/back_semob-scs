from bson import ObjectId
from pymongo import ReturnDocument

from src.app.db.session import client

colecao = client["semob-scs"]["users"]


def create_user(dados: dict):
    resultado = colecao.insert_one(dados)
    return str(resultado.inserted_id)


def get_users():
    resultado = colecao.find({}, {"nome": 1, "email": 1})
    return [
        {"id": str(user["_id"]), "nome": user["nome"], "email": user["email"]}
        for user in resultado
    ]


def get_user_by_id(user_id: str):
    if not ObjectId.is_valid(user_id):
        return None

    resultado = colecao.find_one({"_id": ObjectId(user_id)}, {"nome": 1, "email": 1})
    if resultado is None:
        return None

    return {
        "id": str(resultado["_id"]),
        "nome": resultado["nome"],
        "email": resultado["email"],
    }


def get_users_by_name(name: str):
    resultado = colecao.find(
        {"nome": {"$regex": name, "$options": "i"}}, {"nome": 1, "email": 1}
    )
    return [
        {"id": str(user["_id"]), "nome": user["nome"], "email": user["email"]}
        for user in resultado
    ]


def delete_user_by_id(user_id: str):
    if not ObjectId.is_valid(user_id):
        return None

    user = colecao.find_one_and_delete({"_id": ObjectId(user_id)})
    if user is None:
        return None

    return {
        "id": str(user["_id"]),
        "nome": user["nome"],
        "email": user["email"],
    }


def update_user_by_id(user_id: str, dados: dict):
    if not ObjectId.is_valid(user_id):
        return None

    user = colecao.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": dados},
        {"nome": 1, "email": 1},
        return_document=ReturnDocument.AFTER,
    )
    if user is None:
        return None

    return {
        "id": str(user["_id"]),
        "nome": user["nome"],
        "email": user["email"],
    }


def get_user_by_email(email: str):  # para o service de auth
    if not email:
        return None

    user = colecao.find_one({"email": email})

    if user is None:
        return None

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "senha_hash": user["senha_hash"],
    }
