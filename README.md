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

A API fica em `http://localhost:8000`; a raiz apresenta versão e links úteis,
Swagger fica em `http://localhost:8000/docs` e ReDoc em
`http://localhost:8000/redoc`.

Também é possível subir API e Mongo juntos:

```bash
docker compose up --build
```

O Compose verifica automaticamente `/health/ready`. Use `docker compose ps` para
confirmar que API e MongoDB estão marcados como `healthy` antes de integrar o front.

## Configuração

Copie `.env.example` para `.env`. Em produção, troque `JWT_SECRET_KEY`, restrinja `CORS_ORIGINS` e use uma URI Mongo com autenticação e TLS.

`MONGO_CONNECT_ON_STARTUP=true` valida a conexão e cria os índices ao iniciar. O padrão no código é `false` para permitir testes e inspeção sem um banco disponível.

### Rastreamento de requisições

Toda resposta inclui `X-Request-ID`, que permite relacionar uma chamada do front aos
logs do backend, e `X-Process-Time-Ms`, com o tempo gasto pela API. O front pode enviar
um `X-Request-ID` próprio usando letras, números, ponto, hífen ou sublinhado; valores
inválidos são substituídos por um UUID seguro. Os dois headers são expostos por CORS,
portanto também podem ser lidos pelo aplicativo web.

```bash
curl -i http://localhost:8000/health \
  -H "X-Request-ID: dashboard-carregamento-01"
```

## Endpoints principais

Todas as rotas de negócio usam o prefixo `/api/v1`.

| Grupo | Rotas | Finalidade |
|---|---|---|
| Informações | `GET /` | Versão, prefixo e links de descoberta da API |
| Saúde | `GET /health`, `GET /health/ready` | Verifica processo e dependências da API |
| Autenticação | `POST /auth/login` | Gera JWT Bearer |
| Usuários | `/users` | Cadastro e administração |
| Operação | `/operations` | Frota, viagens e quilometragem por dia/linha |
| Passageiros | `/passengers` | Catraca, antecipados e não pagantes |
| Financeiro | `/financials` | Vendas, utilização, transferências e saldo |
| Alertas | `/alerts`, `POST /alerts/generate` | Ocorrências, acompanhamento e detecção automática de anomalias |
| Dashboard | `GET /dashboard/overview` | KPIs, série diária e ranking de linhas |
| Importação | `POST /imports/smart-report` | Importa HTML e faz upsert idempotente |
| Preferências | `/preferences/me` | Preferências do usuário autenticado |
| Relatórios | `/reports` | Fila preparada para um worker de geração |

As escritas, importações, preferências e relatórios exigem `Authorization: Bearer <token>`. As leituras do painel são públicas por enquanto para facilitar a integração do protótipo Flutter.

### Saúde e prontidão

`GET /health` confirma que o processo da API está funcionando sem consultar serviços
externos. `GET /health/ready` também testa a conexão com o MongoDB e devolve `503`
quando o banco estiver indisponível, permitindo o uso em health checks do Docker,
Kubernetes ou de uma plataforma de hospedagem. As respostas não são armazenadas em
cache e incluem o instante da verificação; a prontidão também informa a latência do
teste do banco. O endpoint antigo `GET /ready` continua disponível como alias
depreciado para não quebrar integrações existentes.

### Importar relatórios existentes

Autentique-se e envie um arquivo por vez como `multipart/form-data`:

```bash
curl -X POST http://localhost:8000/api/v1/imports/smart-report \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "report_type=operations" \
  -F "file=@Mensal_202608.html"
```

Tipos aceitos: `operations`, `passengers` e `financials`. A chave natural de cada série impede duplicação quando um relatório é reenviado.

### Gerar alertas automáticos

Depois de importar ou cadastrar os dados do período, um usuário autenticado pode
executar as regras de detecção:

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/generate?start_date=2026-08-01&end_date=2026-08-31" \
  -H "Authorization: Bearer SEU_TOKEN"
```

Atualmente são avaliados o percentual de viagens concluídas, a proporção de
quilometragem ociosa e o crédito circulante negativo. A execução é idempotente:
reprocessar o mesmo período atualiza a ocorrência existente em vez de duplicá-la.
Alertas automáticos cuja condição deixou de existir são resolvidos, enquanto uma
ocorrência resolvida manualmente não é reaberta pelo reprocessamento.

Os limites podem ser ajustados por ambiente sem alterar código:

| Variável | Padrão | Uso |
|---|---:|---|
| `TRIP_COMPLETION_ALERT_THRESHOLD` | `98.0` | Percentual abaixo do qual há alerta de viagens |
| `TRIP_COMPLETION_CRITICAL_THRESHOLD` | `90.0` | Percentual abaixo do qual o alerta é crítico |
| `DEADHEAD_KM_ALERT_THRESHOLD` | `8.0` | Percentual máximo de quilometragem ociosa |
| `NEGATIVE_CREDIT_CRITICAL_AMOUNT` | `10000` | Déficit a partir do qual o crédito negativo é crítico |

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
