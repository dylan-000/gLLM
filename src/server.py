from fastapi import FastAPI
from chainlit.utils import mount_chainlit
from .routers.authrouter import AuthRouter
from .routers.adminrouter import AdminRouter
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
app.include_router(AuthRouter)
app.include_router(AdminRouter)
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")
