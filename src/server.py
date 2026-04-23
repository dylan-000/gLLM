import json
import os
import time

from chainlit.utils import mount_chainlit
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.core import oauth2_scheme
from src.routers.adminrouter import AdminRouter
from src.routers.authrouter import AuthRouter
from src.services.authservice import require_roles
from src.schema.models import UserRole


app = FastAPI()

# Configure CORS to allow credentials from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "http://localhost:8004",
        "http://127.0.0.1:8004",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(AuthRouter)

admin_deps = []
if os.getenv("MOCK_CONTAINERS", "false").lower() != "true":
    admin_deps = [Depends(oauth2_scheme), Depends(require_roles(UserRole.admin))]

app.include_router(
    AdminRouter,
    dependencies=admin_deps,
)
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")

if os.path.isdir("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
else:
    print("No frontend dist folder detected. Skipping admin UI deployment")
