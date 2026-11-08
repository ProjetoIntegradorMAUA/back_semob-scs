# Backend SEMOB-SCS

API FastAPI + MongoDB para consolidar os dados operacionais do transporte municipal de São Caetano do Sul. O backend cobre autenticação, operação da frota, passageiros, financeiro, alertas, preferências, geração de relatórios, importação Smart Report/Smart Data e todos os agregados consumidos pelo dashboard Flutter.

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
| Análises | `/analytics/operations`, `/passengers`, `/financials` | Contratos completos das telas analíticas |
| Importação | `/imports/smart-report`, `/imports/smart-data`, `/imports/history` | Ingestão idempotente, simulação e auditoria dos lotes |
| Preferências | `/preferences/me` | Preferências do usuário autenticado |
| Relatórios | `/reports`, `/reports/{id}/download` | Geração e download de PDF, Excel e CSV |

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

Tipos aceitos:

- `operations`: operação diária consolidada;
- `operation_lines`: viagens e quilometragem por linha (`Mensal_Linhas`);
- `operation_fcv`: programadas/realizadas por manhã, tarde e noite (`Mensal_FCV`);
- `hourly_operations`: veículos e viagens por hora, consolidado ou por linha;
- `passengers`: catraca, antecipados e não pagantes;
- `financials`: vendas, utilização, transferências e saldo.

A chave natural de cada série impede duplicação quando um relatório é reenviado.
Acrescente `?dry_run=true` para validar e contabilizar o conteúdo sem persistir os
registros. Cada tentativa recebe um identificador e pode ser consultada em
`GET /api/v1/imports/history`, com usuário, origem, checksum, contagens e resultado.

### Integração futura com Smart Data

`POST /api/v1/imports/smart-data` recebe lotes JSON normalizados das quatro séries
(`operations`, `passengers`, `financials` e `hourly_operations`). O endpoint força a
origem `smart_data_api` e utiliza os mesmos upserts, índices e analytics dos HTMLs.
Quando a especificação e as credenciais da Smart Data forem disponibilizadas, será
necessário apenas construir o adaptador externo para esse contrato.
O mesmo endpoint aceita `dry_run` e registra o histórico, permitindo homologar um
adaptador novo antes de liberar gravações no banco de produção.

### Contratos das telas Flutter

As rotas analíticas evitam que o aplicativo replique regras de negócio:

- `/analytics/operations`: KPIs, evolução diária, ranking de linhas e FCV por faixa;
- `/analytics/passengers`: composição, evolução diária/semanal e oferta por hora;
- `/analytics/financials`: vendas/utilização diária, semanal e comparação mensal.

Todas recebem `start_date` e `end_date` no formato `YYYY-MM-DD`.

### Relatórios gerenciais

`POST /api/v1/reports` gera o arquivo imediatamente nos formatos `pdf`, `xlsx` ou
`csv`. Os tipos são `consolidated`, `operations`, `passengers`, `financials` e
`alerts`. O resultado informa `file_url`; somente o solicitante autenticado pode
consultar, baixar ou excluir o relatório. Em Docker, os arquivos ficam no volume
persistente `report_files`.

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

Os testes usam dependências substituídas, arquivos reais gerados em diretório
temporário e mocks de persistência; não precisam de MongoDB ativo. A configuração
atual mantém cobertura acima de 90%.

## Estrutura

```text
src/app/
  api/             rotas e dependências FastAPI
  core/            configuração por ambiente
  db/              sessão Mongo e índices
  models/          documentos de domínio
  schemas/         contratos e validações HTTP
  repositories/    persistência e consultas
  services/        autenticação, analytics, relatórios e parsers de importação
src/test/           testes unitários e de API
```

## Próximas integrações previstas

- conectar o adaptador `/imports/smart-data` à API externa quando houver credenciais;
- mover geração de relatórios muito grandes para worker assíncrono;
- aplicar papéis/permissões (administrador, gestor e leitura);
- mover agregações de grande volume para pipelines MongoDB e cache.
