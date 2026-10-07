# back_semob-scs

Backend Python para integração com o aplicativo Dart/Flutter por meio de uma API HTTP que troca dados em JSON.

## Preparar o ambiente

Na raiz do projeto, crie o ambiente virtual caso ele ainda não exista:

```bash
python3 -m venv venv
```

Ative o ambiente no Bash:

```bash
source ./venv/bin/activate
```

Instale as dependências registradas no projeto:

```bash
python -m pip install -r requirements.txt
```

O `requirements.txt` inclui FastAPI e Uvicorn. O FastAPI define as rotas da API; o Uvicorn executa o servidor.

## Executar a API

Quando houver um arquivo `main.py` com uma instância chamada `app`, execute:

```bash
uvicorn main:app --reload
```

Durante o desenvolvimento, a API ficará disponível em `http://localhost:8000` e a documentação interativa em `http://localhost:8000/docs`.

## Atualizar as dependências

Depois de instalar ou atualizar pacotes no ambiente virtual, gere novamente o arquivo de dependências:

```bash
python -m pip freeze > requirements.txt
```
