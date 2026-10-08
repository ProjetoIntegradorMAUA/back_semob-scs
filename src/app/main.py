from fastapi import FastAPI

from src.app.api.routes.auth import router as auth_router
from src.app.api.routes.user import router as user_router

app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router)

@app.get("/teste")
def get_rota_teste():
    return {"mensagem": "Teste Funcionando"}
