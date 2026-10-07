from fastapi import FastAPI

app = FastAPI()


@app.get("/teste")
def get_rota_teste():
    return {"mensagem": "Teste Funcionando"}
