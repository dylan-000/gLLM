import json
import os
import time

from chainlit.utils import mount_chainlit
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.core import oauth2_scheme
from src.routers.adminrouter import AdminRouter
from src.routers.authrouter import AuthRouter
from src.routers.finetunerouter import FineTuneRouter
from src.services.authservice import require_roles_from_cookie
from src.schema.models import UserRole


app = FastAPI()

# Configure CORS to allow credentials from frontend
# NOTE: Both localhost and 127.0.0.1 variants are required — browsers treat
# them as distinct origins, and port-forwarded remote sessions typically
# resolve to localhost while the server binds on 127.0.0.1.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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

app.include_router(
    AdminRouter,
    dependencies=admin_deps,
)
app.include_router(FineTuneRouter)
mount_chainlit(app=app, target="./chainlit-app.py", path="/gllm")

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "../frontend/dist")

if os.path.isdir(FRONTEND_DIST):
    # Serve Vite-hashed JS/CSS bundles from dist/assets/
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    # Serve public root files (logo, favicon, etc.) that Vite copies to dist/.
    # Mounted BEFORE the catch-all so these files are found as real static files
    # instead of being swallowed by the SPA fallback.
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST), name="static-root")

    # Catch-all: serve index.html for any path not matched by API routers above.
    # This allows React's BrowserRouter to handle client-side routing on
    # hard refresh, back/forward navigation, and direct URL entry.
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index)
else:
    print("No frontend dist folder detected. Skipping admin UI deployment")
