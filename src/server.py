from .routers.authrouter import AuthRouter
from .routers.adminrouter import AdminRouter
from chainlit.utils import mount_chainlit
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from .core.core import oauth2_scheme

app = FastAPI()

# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
app.include_router(AuthRouter)
app.include_router(AdminRouter, dependencies=[Depends(oauth2_scheme)])
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")
