from fastapi import FastAPI, Depends
from chainlit.utils import mount_chainlit
from .Routers.AuthRouter import AuthRouter

app = FastAPI()
app.include_router(AuthRouter)
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")
