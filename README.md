# EloquentAI Backend

FastAPI backend for EloquentAI. It provides:

- Auth (signup, login)
- Conversation + message store (SQLite by default via SQLModel)
- Chat endpoint that retrieves context from Pinecone and generates responses via OpenAI
- Simple content guardrails and prompt shaping

> Status: Prototype. Intended for dev/demo. See Security notes for hardening before running in production.

## Requirements

- Python 3.11+
- OpenAI API key
- Pinecone API key and index host

## Quick start (local)

```bash
# from backend/
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .

# Create your .env (see Configuration below)
cp .env.example .env  # if you create the example first

# Run dev server (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Open API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Create a `.env` file in `backend/` (loaded by `dotenv`).

Environment variables:

- `DATABASE_URL` (default: `sqlite:///./chat.db`)
- `OPENAI_API_KEY` (required)
- `PINECONE_API_KEY` (required)
- `PINECONE_HOST` (required)
- `PINECONE_NAMESPACE` (optional, default: `__default__`)

Example `.env`:

```env
DATABASE_URL=sqlite:///./chat.db
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcn-...
PINECONE_HOST=your-index-host
PINECONE_NAMESPACE=__default__
```

Notes:

- The SQLite DB file `chat.db` is created on first run. Do not commit it.
- For production, use a managed database (Postgres/MySQL) instead of SQLite.

## Run (production)

Run behind a process manager / container with Gunicorn + Uvicorn workers:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 main:app
```

Adjust workers based on CPU and workload. Disable docs in prod via FastAPI settings or a reverse proxy if needed.

## Docker (optional)

If you containerize this service, a minimal Dockerfile might look like:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN pip install -U pip && pip install -e .
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

Build and run:

```bash
docker build -t eloquentai-backend .
docker run --env-file .env -p 8000:8000 eloquentai-backend
```

Ensure the `.env` you pass in the container includes all required variables.

## API overview

- Health
  - GET `/health` → `{ "status": "healthy" }`

- Auth
  - POST `/api/auth/signup` — create user
  - POST `/api/auth/login` — login user

- Chat
  - POST `/api/chat/create` — upsert conversation and generate assistant reply
  - GET `/api/chat/messages/{conversation_id}` — list chat history
  - GET `/api/chat/conversations?user_id={id}` — list user conversations
  - POST `/api/chat/delete/{conversation_id}` — soft-delete a conversation
  - POST `/api/chat/summarize/{conversation_id}` — summarize a conversation

### Schemas (selected)

Signup (request):

```json
{
  "email": "alice@example.com",
  "name": "Alice",
  "password": "secret"
}
```

Login (request):

```json
{
  "email": "alice@example.com",
  "password": "secret"
}
```

Chat create (request):

```json
{
  "user_id": 1,
  "conversation_id": null,
  "message": "How do I reset my password?"
}
```

Response wrapper:

```json
{
  "data": { ... },
  "status_code": 200
}
```

## Examples

```bash
# Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","name":"Alice","password":"secret"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}'

# Chat
curl -X POST http://localhost:8000/api/chat/create \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1, "conversation_id":null, "message":"How do I reset my password?"}'
```

## Architecture at a glance

- `src/routers/*`: FastAPI route handlers
- `src/controllers/*`: data access and domain logic
- `src/sql_models/*`: SQLModel ORM entities
- `src/models/*`: Pydantic request/response models
- `src/helpers/*`: integrations (DB session, OpenAI, Pinecone), guardrails, utilities
- `src/constants/*`: prompts and roles

## Security notes (read before prod)

- CORS is permissive in `main.py` for dev. Restrict `allow_origins` and only enable `allow_credentials` with explicit origins.
- Authentication/authorization: endpoints currently trust `user_id` provided by clients and do not issue tokens. Implement JWT and enforce ownership checks for conversations before exposing publicly.
- Do not index or log secrets. Ensure `.env` is not committed.
- Sanitize retrieved context: run guardrails on Pinecone context before prompting the model.
- Rate limit login/chat endpoints and return generic login errors (avoid user enumeration).

## Development

- Tables are created automatically on first DB access. For production, prefer Alembic migrations and a managed DB.
- Code style: Python 3.11 + type hints. FastAPI + SQLModel.

## Troubleshooting

- Missing OpenAI/Pinecone credentials → verify `.env` and that the service can reach external APIs.
- SQLite locking on macOS/Windows → run a single worker in dev or switch to Postgres for concurrency.

## License

Proprietary – All rights reserved (update as appropriate).

# EloquentAI Backend

FastAPI backend with SQLModel (SQLite by default), simple auth, and a chat endpoint that uses OpenAI and Pinecone for context-aware responses.

## Quick start
```bash
# from backend/
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- Open API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration
Create a `.env` file in `backend/` (loaded by `dotenv`).

- `DATABASE_URL` (default: `sqlite:///./chat.db`)
- `OPENAI_API_KEY` (required)
- `PINECONE_API_KEY` (required)
- `PINECONE_HOST` (required)
- `PINECONE_NAMESPACE` (optional, default: `__default__`)

Example `.env`:
```env
DATABASE_URL=sqlite:///./chat.db
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcn-...
PINECONE_HOST=your-index-host
PINECONE_NAMESPACE=__default__
```

## API overview
- Health
  - GET `/health` → `{ "status": "healthy" }`
- Auth
  - POST `/api/auth/signup` — create user
  - POST `/api/auth/login` — login user
- Chat
  - POST `/api/chat/create` — upsert conversation and generate assistant reply
  - GET `/api/chat/messages/{conversation_id}` — list chat history
  - GET `/api/chat/conversations?user_id={id}` — list user conversations

## Examples
```bash
# Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","name":"Alice","password":"secret"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}'

# Chat
curl -X POST http://localhost:8000/api/chat/create \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1, "conversation_id":null, "message":"How do I reset my password?"}'
```

## Notes
- SQLite DB file `chat.db` is created automatically on first run.
- Passwords are hashed with `bcrypt`.
- CORS is permissive in `main.py` and can be restricted as needed.
- `EmailStr` requires `email-validator` (already included in dependencies).
