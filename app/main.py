from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router as api_router

app = FastAPI()

# Session Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key"
)

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include API router
app.include_router(api_router)