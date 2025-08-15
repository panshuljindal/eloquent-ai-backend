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
