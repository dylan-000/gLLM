# Welcome to gLLM

### Project Structure
```python
.
├── DEV_GUIDE.md          
├── docker-compose.yaml
├── frontend                        # dashboard frontend sourcecode
│   ├── components.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── public
│   │   └── gLLM_ICON.png
│   ├── README.md
│   ├── src
│   │   ├── App.tsx
│   │   ├── assets
│   │   ├── components
│   │   ├── contexts
│   │   ├── index.css
│   │   ├── lib
│   │   ├── main.tsx
│   │   ├── models
│   │   └── pages
│   ├── tailwind.config.js
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── vite.env-d.ts
├── package-lock.json
├── README.md
├── src                             
│   ├── chainlit-app.py             # chainlit configuration
│   ├── chainlit.md 
│   ├── core                        # global app configs
│   │   ├── config.py
│   │   ├── core.py
│   │   └── __init__.py
│   ├── db                          # database and session management
│   │   ├── database.py
│   │   └── __init__.py
│   ├── DOCKERFILE
│   ├── __init__.py
│   ├── models                      # DTO pydantic models for the FastApi endpoints
│   │   ├── auth.py
│   │   ├── __init__.py
│   │   └── user.py
│   ├── public
│   │   ├── favicon.ico
│   │   ├── logo_dark.png
│   │   ├── logo_light.png
│   │   └── theme.json
│   ├── pyproject.toml
│   ├── routers                     # FastApi router definitions
│   │   ├── adminrouter.py
│   │   ├── authrouter.py
│   │   └── __init__.py
│   ├── schema                      # SQLAlchemy data models and db schema definition
│   │   ├── alembic                 # Migration tracking
│   │   ├── alembic.ini
│   │   ├── __init__.py
│   │   └── models.py  
│   ├── server.py                   # FastApi app entry point
│   ├── services                    # Service functions
│   │   ├── adminservice.py
│   │   ├── authservice.py
│   │   ├── promptservice.py
│   │   └── ragutils
│   └── uv.lock
├── tests                           # Test Suites
│   ├── authservice_tests.py
│   ├── conftest.py
│   ├── judge_config.py
│   ├── pyproject.toml
│   ├── README.md
│   ├── test_ai_quality.py
│   ├── test_integration.py
│   ├── test_unit.py
│   └── uv.lock
└── vllmconfig
    ├── vllminit.sh
    └── vllm-logs
        └── vllm.log
```


### Sequential Steps for Running the System
Assumptions:
1. You have an OpenAI Api compatible inference server running on localhost:8000.
2. Your system has Docker installed.
3. You have an AWS S3 bucket and the appropriate connection information.
4. You have `uv` installed on your system.

Steps:
1. Clone the project.
2. `cd` into `./src/` and run `uv sync` to install the dependencies for the project. Now activate the virtual environment that `uv` created. On Mac/Linux, run `source .venv/bin/activate` (or `venv/bin/activate`). On Windows, run `.\.venv\Scripts\activate` (or `.\venv\Scripts\activate`). This allows you to use the dependencies and scripts you downloaded with the `uv sync` command.
3. Add an `.env` file directly inside the `./src/` directory exactly (i.e. `./src/.env`). It will not be detected if it is in the project root. It should at least contain the following variables: 
```
DATABASE_URL=
BUCKET_NAME=
APP_AWS_ACCESS_KEY=
APP_AWS_SECRET_KEY=
APP_AWS_REGION=
AUTH_SECRET=
ACCESS_TOKEN_EXPIRE_MINUTES=
HASH_ALGORITHM=
CHAINLIT_AUTH_SECRET=
```
4. Now, in the project root, ensure your Docker Engine (e.g., Docker Desktop) is fully booted and running. Then run `docker-compose up -d` (add `sudo` if on Linux) to compose up the project PostgreSQL database and ChromaDB containers respectively. 
    *Troubleshooting Note:* On Windows, you might need to use `127.0.0.1` instead of `localhost` in your `DATABASE_URL` string inside `.env` to avoid IPv6 authentication errors. Additionally, ensure you don't have a native PostgreSQL Windows service already intercepting port 5432.
5. If that went well, you now have the database and vector database up and running. You still need to *apply* the schema to the database because it doesn't have any tables as is.
6. To apply the database schema to your fresh database, `cd` into `./src/schema/` and run `uv run alembic upgrade head`. Using `uv run` ensures the correct environment is executed even if you didn't manually activate it. If you have the right connection information in your `.env` variables, this should work.
7. Now before we start the backend server to startup the llm interface, we're going to build the frontend so that our backend at least has something to serve at its root. `cd` into `./frontend/`.
8. run `npm i` to install the dependencies.
9. Set the port you want to use for local testing in the `.env.local` file. For example, `VITE_API_PORT=8004`. There should also be a `.env` file in the `./frontend/` directory for holding the default port at `VITE_API_PORT=8001`.
10. run `npm run build` to build the project.
11. `cd` back into `./src/` and run `fastapi dev server.py --port 8001` (or other port if 8001 is in use, make sure this is the same as `VITE_API_PORT` in your `.env.local` file) to start the dev mode for the backend. It's important that we specify port 8001 because it would default to 8000 otherwise and conflict with the inference endpoints that we are expecting to be at that port.