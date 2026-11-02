# Backend SEMOB-SCS

API FastAPI + MongoDB para consolidar os dados operacionais do transporte municipal de São Caetano do Sul. O backend cobre autenticação, operação da frota, passageiros, financeiro, alertas, preferências, pedidos de relatórios, importação dos HTMLs da Smart Report e agregação do dashboard.

## Requisitos

- Python 3.11 ou superior
- MongoDB 7 ou superior, ou Docker com Compose

## Executar localmente

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn src.app.main:app --reload
```

No Bash:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
uvicorn src.app.main:app --reload
```

A API fica em `http://localhost:8000`; Swagger em `http://localhost:8000/docs` e ReDoc em `http://localhost:8000/redoc`.

Também é possível subir API e Mongo juntos:

```bash
docker compose up --build
```

## Configuração

Copie `.env.example` para `.env`. Em produção, troque `JWT_SECRET_KEY`, restrinja `CORS_ORIGINS` e use uma URI Mongo com autenticação e TLS.

`MONGO_CONNECT_ON_STARTUP=true` valida a conexão e cria os índices ao iniciar. O padrão no código é `false` para permitir testes e inspeção sem um banco disponível.

## Endpoints principais

Todas as rotas de negócio usam o prefixo `/api/v1`.

| Grupo | Rotas | Finalidade |
|---|---|---|
| Autenticação | `POST /auth/login` | Gera JWT Bearer |
| Usuários | `/users` | Cadastro e administração |
| Operação | `/operations` | Frota, viagens e quilometragem por dia/linha |
| Passageiros | `/passengers` | Catraca, antecipados e não pagantes |
| Financeiro | `/financials` | Vendas, utilização, transferências e saldo |
| Alertas | `/alerts` | Ocorrências, gravidade e acompanhamento |
| Dashboard | `GET /dashboard/overview` | KPIs, série diária e ranking de linhas |
| Importação | `POST /imports/smart-report` | Importa HTML e faz upsert idempotente |
| Preferências | `/preferences/me` | Preferências do usuário autenticado |
| Relatórios | `/reports` | Fila preparada para um worker de geração |

As escritas, importações, preferências e relatórios exigem `Authorization: Bearer <token>`. As leituras do painel são públicas por enquanto para facilitar a integração do protótipo Flutter.

### Importar relatórios existentes

Autentique-se e envie um arquivo por vez como `multipart/form-data`:

```bash
curl -X POST http://localhost:8000/api/v1/imports/smart-report \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "report_type=operations" \
  -F "file=@Mensal_202608.html"
```

Tipos aceitos: `operations`, `passengers` e `financials`. A chave natural de cada série impede duplicação quando um relatório é reenviado.

## Testes

```bash
python -m pytest
python -m pytest --cov=src.app --cov-report=term-missing
```

Os testes usam dependências substituídas e mocks; não precisam de MongoDB ativo.

## Estrutura

```text
src/app/
  api/             rotas e dependências FastAPI
  core/            configuração por ambiente
  db/              sessão Mongo e índices
  models/          documentos de domínio
  schemas/         contratos e validações HTTP
  repositories/    persistência e consultas
  services/        autenticação, agregação e parser Smart Report
src/test/           testes unitários e de API
```

## Próximas integrações previstas

- substituir o upload manual por ingestão direta da API Smart Data;
- executar pedidos de relatório em worker assíncrono e gravar `file_url`;
- aplicar papéis/permissões (administrador, gestor e leitura);
- mover agregações de grande volume para pipelines MongoDB e cache.
