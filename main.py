from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import dotenv
from src.routers.chat import router as chat_router
from src.routers.auth import router as auth_router
from src.helpers.response import api_response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
app = FastAPI(
    title="Eloquent AI Agent",
    description="A Chat application for Eloquent AI",
    version="1.0.0"
)

dotenv.load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return api_response({"message": exc.detail}, exc.status_code)

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return api_response({"message": "Validation error", "errors": exc.errors()}, 422)

@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    return api_response({"message": "Internal Server Error"}, 500)

@app.get("/health")
def health_check():
    return api_response({"status": "healthy"})

@app.get("/")
def root():
    return api_response({"message": "Hello World"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
