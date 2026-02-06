from fastapi import FastAPI
from chainlit.utils import mount_chainlit
from .Data.database import SessionLocal, engine
from .Routers.AuthRouter import AuthRouter

app = FastAPI()

app.include_router(AuthRouter)

mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")
