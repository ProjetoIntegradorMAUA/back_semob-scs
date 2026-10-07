from fastapi import FastAPI

from src.app.api.routes.user import router as user_router

app = FastAPI()

app.include_router(user_router)

@app.get("/teste")
def get_rota_teste():
    return {"mensagem": "Teste Funcionando"}
