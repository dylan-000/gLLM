from .routers.authrouter import AuthRouter
from .routers.adminrouter import AdminRouter
from chainlit.utils import mount_chainlit
from fastapi import FastAPI, Depends, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from .core.core import oauth2_scheme
import os
import json
import time

app = FastAPI()

app.include_router(AuthRouter)
app.include_router(AdminRouter, dependencies=[Depends(oauth2_scheme)])
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")

if os.path.isdir(
    "../frontend/dist"
):  # HIGHLY IMPORTANT THAT THIS IS LAST. It will otherwise conflict with all of the other API paths.
    app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
else:
    print("No frontend dist folder detected. Skipping admin UI deployment")
