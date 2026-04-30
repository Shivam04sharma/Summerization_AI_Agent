# Summerization_AI_Agent

> AI-powered Text Summarization & Narrative Generation Service

A production-ready FastAPI microservice built as **Summerization_AI_Agent** for AI-powered text summarization and narrative generation, powered by **Google Gemini (Vertex AI)** or **OpenAI** as fallback.

---

## Screenshots

> Screenshots are available in the `assets/` folder.

| Swagger UI | Summarize API | Summary Types |
|---|---|---|
| ![Swagger UI](assets/swagger_ui.png) | ![Summarize](assets/summarize_api.png) | ![Types](assets/summary_types.png) |

---

## Features

- Text summarization with configurable summary types (bullet, tldr, narrative, etc.)
- Multi-language output support (English, Hindi, Punjabi, Marathi)
- Dynamic prompt management via PostgreSQL
- Auto DB migrations on startup
- gRPC server support
- JWT auth (enable/disable via config)
- Langfuse observability integration
- Swagger UI (debug mode)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL (asyncpg) |
| LLM | Google Gemini (Vertex AI) / OpenAI |
| Auth | JWT (PyJWT) |
| Observability | Langfuse |
| RPC | gRPC |
| Config | Pydantic Settings |
| Logging | Structlog |

---

## Project Structure

```
Summerization_AI_Agent/
├── src/
│   ├── main.py                        # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py                # Env-based config loader
│   │   ├── auth.py                    # JWT auth dependency
│   │   ├── config_local.py            # Local environment settings
│   │   ├── config_dev.py              # Dev environment settings
│   │   └── config_beta.py             # Beta environment settings
│   ├── db/
│   │   ├── session.py                 # asyncpg pool + migrations runner
│   │   ├── models.py                  # DB models
│   │   └── migrations/
│   │       ├── local/                 # SQL migrations for local env
│   │       ├── dev/                   # SQL migrations for dev env
│   │       └── beta/                  # SQL migrations for beta env
│   ├── routes/
│   │   └── summarize_routes.py        # Summarization + summary type CRUD routes
│   ├── schemas/
│   │   └── summarize_schemas.py       # Pydantic request/response schemas
│   └── services/
│       ├── summarization_engine.py    # Core summarization business logic
│       ├── llm_client.py              # Gemini + OpenAI LLM clients
│       ├── prompt_store.py            # DB-backed prompt/config store
│       ├── grpc_server.py             # gRPC server lifecycle
│       └── grpc_summarize_service.py  # gRPC service implementation
├── Dockerfile
├── requirements.txt
├── .env.example                       # Environment variable template
└── README.md
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker (optional)
- Google Cloud account with Vertex AI enabled **OR** OpenAI API key

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Summerization_AI_Agent.git
cd Summerization_AI_Agent

> All commands below assume you are inside the `Summerization_AI_Agent/` root directory.
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values (see [Environment Variables](#environment-variables) section below).

### 5. Create PostgreSQL database

```bash
# Connect to PostgreSQL and create the database
psql -U postgres -c "CREATE DATABASE ai_platform_local;"
```

### 6. Run the server

```bash
cd src
uvicorn main:app --host 0.0.0.0 --port 9003 --reload
```

Server will be available at: `http://localhost:9003`  
Swagger UI: `http://localhost:9003/docs`  
Health check: `http://localhost:9003/health`

---

## Environment Variables

Create a `.env` file in the project root. Use `.env.example` as template:

```env
# ── App ───────────────────────────────────────────────────────────────────────
ENV=local
SERVICE_NAME=oni-summarization
PORT=9003
LOG_LEVEL=debug
DEBUG=true

# ── Database ──────────────────────────────────────────────────────────────────
DB_USERNAME=<your_db_username>
DB_PASSWORD=<your_db_password>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=<your_database_name>
DB_SCHEMA=<your_schema_name>

# ── LLM Provider ─────────────────────────────────────────────────────────────
# Options: gemini | openai
INTENT_ROUTER_PROVIDER=gemini

# ── Vertex AI / Gemini ────────────────────────────────────────────────────────
GOOGLE_APPLICATION_CREDENTIALS=<path_to_your_service_account_json>
VERTEX_AI_PROJECT_ID=<your_gcp_project_id>
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash
GCP_PRIVATE_KEY_ID=<your_gcp_private_key_id>
GCP_PRIVATE_KEY=<your_gcp_private_key>
GCP_CLIENT_EMAIL=<your_service_account_email>
GCP_CLIENT_ID=<your_gcp_client_id>

# ── OpenAI (fallback) ─────────────────────────────────────────────────────────
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_MODEL=gpt-4o-mini

# ── Summarization Engine ──────────────────────────────────────────────────────
SUMMARIZATION_MAX_INPUT_TOKENS=32000
SUMMARIZATION_MAX_OUTPUT_TOKENS=2048
SUMMARIZATION_TEMPERATURE=0.3
NARRATIVE_TEMPERATURE=0.5

# ── Auth ──────────────────────────────────────────────────────────────────────
AUTH_ENABLED=false
ONIFIED_JWT_SECRET_KEY=<your_jwt_secret>
JWT_ALGORITHM=HS256

# ── Langfuse Observability (optional) ────────────────────────────────────────
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=<your_langfuse_public_key>
LANGFUSE_SECRET_KEY=<your_langfuse_secret_key>
LANGFUSE_HOST=http://localhost:3000

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Docker Setup

### Build the image

```bash
# Run from inside Summerization_AI_Agent/ root
docker build -t summerization-ai-agent .
```

### Run with Docker

```bash
docker run -d \
  --name summerization-ai-agent \
  -p 9003:9003 \
  --env-file .env \
  summerization-ai-agent
```

### Run with Docker Compose

Create a `docker-compose.yml`:

```yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "9003:9003"
    env_file:
      - .env
    depends_on:
      - postgres

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_platform_local
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Then run:

```bash
docker compose up -d
```

---

## API Reference

### Health Check

```
GET /health
GET /actuator/health
```

### Summarization

#### Summarize text

```
POST /api/v1/summarize
```

Request body:
```json
{
  "text": "Your long text to summarize goes here...",
  "summaryType": "narrative",
  "language": "en"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| text | string | Yes | Input text (max 100,000 chars) |
| summaryType | string | No | Key of summary type. Uses default if omitted |
| language | string | No | Output language: `en`, `hi`, `pa`, `mr`. Default: `en` |

Response:
```json
{
  "summary": "Generated summary text...",
  "word_count": 120,
  "summary_type": "narrative",
  "label": "Narrative Summary",
  "format": "paragraph",
  "model_used": "gemini/gemini-2.0-flash",
  "confidence_score": 0.92
}
```

---

### Summary Type Management

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/summarize/types` | List all active summary types |
| GET | `/api/v1/summarize/types/all` | List all summary types including inactive |
| GET | `/api/v1/summarize/types/{key}` | Get a single summary type |
| POST | `/api/v1/summarize/types` | Create a new summary type |
| PUT | `/api/v1/summarize/types/{key}` | Update an existing summary type |
| DELETE | `/api/v1/summarize/types/{key}` | Delete a summary type |

#### Create Summary Type — Request body

```json
{
  "key": "bullet_short",
  "label": "Short Bullet Points",
  "intent": "bullet",
  "format": "bullet",
  "min_words": 30,
  "max_words": 100,
  "instruction": "Summarize the text in 3-5 concise bullet points.",
  "style_hint": "formal",
  "is_default": false,
  "is_active": true
}
```

---

## DB Migrations

Migrations run automatically on startup. SQL files are located in:

```
src/db/migrations/{env}/V{n}__{description}.sql
```

- `{env}` → `local`, `dev`, or `beta` (based on `ENV` in `.env`)
- Files are applied in version order
- Already applied migrations are skipped (tracked in `schema_migrations` table)

---

## LLM Providers

| Provider | Config value | Notes |
|---|---|---|
| Google Gemini | `gemini` | Requires Vertex AI service account |
| OpenAI | `openai` | Falls back to Gemini on rate limit |

Set `INTENT_ROUTER_PROVIDER` in `.env` to switch providers.

---

## Authentication

JWT auth is disabled by default (`AUTH_ENABLED=false`).

To enable:
1. Set `AUTH_ENABLED=true` in `.env`
2. Set `ONIFIED_JWT_SECRET_KEY` to your secret
3. Pass `Authorization: Bearer <token>` header in all requests

---

## .gitignore Recommendation

Make sure these are in your `.gitignore` before pushing to GitHub:

```
.env
*.pem
*.key
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
```

---

## Privacy & Data Handling (DPDP Aligned)

This service is designed with data privacy in mind and can be aligned with the **Digital Personal Data Protection (DPDP) Act**:

- No user data is stored — input text is processed in-memory and discarded after summarization
- No PII (Personally Identifiable Information) is logged
- LLM providers (Gemini / OpenAI) are called over HTTPS — no plaintext transmission
- Auth is JWT-based and stateless — no session data stored
- Database stores only summarization configuration (prompts/types) — not user content
- Langfuse observability is optional and disabled by default (`LANGFUSE_ENABLED=false`)
- All credentials are environment-variable driven — no hardcoded secrets

> Any organization can deploy this service and configure it to meet their own data residency and privacy compliance requirements.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "feat: your feature description"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

MIT License
