from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def get_route():
    return {"mensagem": "Funcionando"}