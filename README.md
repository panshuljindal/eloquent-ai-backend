# EloquentAI Backend

FastAPI backend for EloquentAI. It provides:

- Auth (signup, login, me) with JWT
- Conversation + message store (SQLite by default via SQLModel)
- Chat endpoints with context retrieval from Pinecone and responses via OpenAI
- Streaming (SSE) and WebSocket chat
- Basic guardrails and prompt shaping

## Requirements

- Python 3.11+
- OpenAI API key
- Pinecone API key and index host

## Quick start (local)

```bash
# from backend/
uv sync
source .venv/bin/activate

# Create your .env (see Configuration below)
# If you maintain an example file:
# cp .env.example .env

# Run dev server (auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Create a `.env` file in `backend/` (loaded by `dotenv`).

Environment variables:

- `DATABASE_URL` (default: `sqlite:///./chat.db`)
- `OPENAI_API_KEY` (required)
- `PINECONE_API_KEY` (required)
- `PINECONE_HOST` (required)
- `PINECONE_NAMESPACE` (optional, default: `__default__`)
- `JWT_SECRET` (optional, default: `eloquentaioperator`)
- `JWT_ALGORITHM` (optional, default: `HS256`)
- `JWT_EXPIRE_MINUTES` (optional, default: `60`)

Example `.env`:

```env
DATABASE_URL=sqlite:///./chat.db
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=pcn-...
PINECONE_HOST=your-index-host
PINECONE_NAMESPACE=__default__
JWT_SECRET=replace-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Notes:

- The SQLite DB file `chat.db` is created on first run. Do not commit it.
- For production, use a managed database (Postgres/MySQL) instead of SQLite.

## Run (production)

Run behind a process manager / container with Gunicorn + Uvicorn workers:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 main:app
```

Tune worker count based on CPU and workload.

## Docker (optional)

Minimal example using pip to install runtime deps:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY . .
RUN pip install -U pip \
 && pip install fastapi uvicorn gunicorn bcrypt email-validator json-repair openai pinecone pydantic sqlmodel guardrails-ai PyJWT websockets python-dotenv
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

Build and run:

```bash
docker build -t eloquentai-backend .
docker run --env-file .env -p 8000:8000 eloquentai-backend
```

## API overview

- Health
  - GET `/health` → `{ "status": "healthy" }`

- Auth
  - POST `/api/auth/signup` — create user, returns `access_token`
  - POST `/api/auth/login` — login, returns `access_token`
  - GET `/api/auth/me` — current user (requires `Authorization: Bearer <token>`) 

- Chat
  - POST `/api/chat/create` — upsert conversation and generate assistant reply
  - POST `/api/chat/stream` — stream assistant reply via SSE
  - WebSocket `/api/chat/ws/{conversation_id}` — stream assistant tokens
  - GET `/api/chat/messages/{conversation_id}` — list chat history
  - GET `/api/chat/conversations` — list current user's conversations (auth required)
  - POST `/api/chat/delete/{conversation_id}` — soft-delete a conversation
  - POST `/api/chat/summarize/{conversation_id}` — summarize a conversation

### Request/response wrapper

All responses are wrapped as:

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

# Login → capture token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret"}' | jq -r '.data.access_token')

# Me (requires auth)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me

# Create or continue a chat (auth optional)
curl -X POST http://localhost:8000/api/chat/create \
  -H 'Content-Type: application/json' \
  -d '{"conversation_id":null, "message":"How do I reset my password?"}'

# Stream via SSE
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"conversation_id":null, "message":"Tell me a joke"}'

# List my conversations (auth required)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/chat/conversations
```

WebSocket (JavaScript example):

```js
const token = "<your_jwt>";
const conversationId = 1; // or create first via /api/chat/create
const ws = new WebSocket(`ws://localhost:8000/api/chat/ws/${conversationId}?token=${token}`);
ws.onmessage = (e) => console.log("delta:", e.data);
ws.onopen = () => ws.send(JSON.stringify({ message: "Hi there" }));
```

## Architecture at a glance

- `src/routers/*`: FastAPI route handlers
- `src/controllers/*`: data access and domain logic
- `src/sql_models/*`: SQLModel ORM entities
- `src/models/*`: Pydantic request/response models
- `src/helpers/*`: DB session, OpenAI, Pinecone, JWT, guardrails, response helpers
- `src/constants/*`: prompts and roles

## Security notes (read before prod)

- CORS is permissive in `main.py` for dev. Restrict `allow_origins` in production.
- JWT is issued on signup/login. Protect sensitive routes and verify ownership (conversation/user) on the server.
- Do not log secrets. Ensure `.env` is not committed. Rotate `JWT_SECRET` regularly.
- Sanitize retrieved context and outputs. Guardrails are provided as a baseline.
- Rate limit login/chat and use generic login errors (prevent enumeration).

## Development

- Tables are created automatically on first DB access. For production, prefer Alembic migrations and a managed DB.
- Code style: Python 3.11 + type hints. FastAPI + SQLModel.

## Troubleshooting

- Missing OpenAI/Pinecone credentials → verify `.env` and outbound network.
- SQLite locking on macOS/Windows → run a single worker in dev or switch to Postgres for concurrency.

## License

Proprietary – All rights reserved (update as appropriate).
