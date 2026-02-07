from fastapi import FastAPI, Depends
from chainlit.utils import mount_chainlit
from .Routers.AuthRouter import AuthRouter
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
app.include_router(AuthRouter)
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")
