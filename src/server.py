import json
import os
import time

from chainlit.utils import mount_chainlit
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.core import oauth2_scheme
from src.routers.adminrouter import AdminRouter
from src.routers.authrouter import AuthRouter


app = FastAPI()

app.include_router(AuthRouter)
app.include_router(AdminRouter, dependencies=[Depends(oauth2_scheme)])
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")

if os.path.isdir("../frontend/dist"):
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
else:
    print("No frontend dist folder detected. Skipping admin UI deployment")
