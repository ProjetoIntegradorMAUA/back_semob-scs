from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.server_api import ServerApi

config = dotenv_values(".env")

client = MongoClient(config["MONGO_URI"], server_api=ServerApi("1"))

try:
    client.admin.command("ping")
    print("Conectado ao MongoDB")
except Exception as e:  # noqa: BLE001
    print(e)
