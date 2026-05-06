# Welcome to gLLM

### Project Structure
```
.
├── DEV_GUIDE.md
├── docker-compose.yaml          # Core services: PostgreSQL + ChromaDB
├── docker-compose.models.yaml   # GPU services: vLLM + Unsloth
├── frontend/                    # React/Vite dashboard frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── models/
│   │   └── pages/
│   ├── package.json
│   └── vite.config.ts
├── langfuse_container/          # Langfuse observability stack
│   └── docker-compose.yml
├── README.md
├── src/                         # FastAPI backend
│   ├── chainlit-app.py          # Chainlit chat interface (mounted at /gllm)
│   ├── core/                    # App config and shared utilities
│   │   └── config.py
│   ├── db/                      # Database session management
│   ├── DOCKERFILE
│   ├── models/                  # Pydantic DTOs for FastAPI endpoints
│   ├── routers/                 # FastAPI router definitions
│   │   ├── adminrouter.py
│   │   ├── authrouter.py
│   │   └── finetunerouter.py
│   ├── schema/                  # SQLAlchemy models + Alembic migrations
│   │   ├── alembic/
│   │   ├── alembic.ini
│   │   └── models.py
│   ├── server.py                # FastAPI app entry point
│   ├── services/                # Business logic
│   │   ├── adminservice.py
│   │   ├── authservice.py
│   │   ├── promptservice.py
│   │   └── ragutils/
│   ├── tools/                   # LLM tool definitions
│   ├── pyproject.toml
│   └── uv.lock
├── tests/                       # Test suites
│   ├── test_unit.py
│   ├── test_integration.py
│   ├── test_ai_quality.py
│   └── conftest.py
└── vllmconfig/
    └── vllminit.sh
```

---

### Service Port Map

| Service              | Port  | Notes                                          |
|----------------------|-------|------------------------------------------------|
| FastAPI backend      | 8001  | Main application server                        |
| Vite dev server      | 5173  | Frontend development only (proxies to 8001)    |
| vLLM inference       | 8000  | OpenAI-compatible API (requires NVIDIA GPU)    |
| ChromaDB             | 8003  | Vector database                                |
| PostgreSQL (app)     | 5432  | Main application database                      |
| Langfuse UI          | 3000  | Observability dashboard (optional)             |
| Unsloth (Jupyter)    | 8002  | Fine-tuning notebooks (requires NVIDIA GPU)    |
| Langfuse PostgreSQL  | 5433  | Langfuse's own database (isolated port)        |

---

### Prerequisites

- **Docker Desktop** (or Docker Engine on Linux)
- **`uv`** – Python package manager: https://docs.astral.sh/uv/getting-started/installation/
- **Node.js 18+** and **npm**
- **NVIDIA GPU + drivers** (only required for vLLM / Unsloth)
- **AWS S3 bucket** with an IAM user that has read/write access
- **HuggingFace account** with a token that can access the model you want to serve (only required for vLLM)

---

### Setup

#### 1. Clone the repository

```bash
git clone <repo-url>
cd gLLM
```

#### 2. Create the backend `.env` file

Create a file at `./src/.env`. The config loader resolves the path relative to `src/core/config.py`, so it **must** be inside `src/`.

```env
# PostgreSQL connection string.
# On Windows, use 127.0.0.1 instead of localhost to avoid IPv6 auth errors.
DATABASE_URL=postgresql://root:root@localhost:5432/postgres

# AWS S3 for file storage
BUCKET_NAME=your-bucket-name
APP_AWS_ACCESS_KEY=your-access-key
APP_AWS_SECRET_KEY=your-secret-key
APP_AWS_REGION=us-east-1

# JWT auth — generate AUTH_SECRET with: openssl rand -hex 32
AUTH_SECRET=your-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
HASH_ALGORITHM=HS256

# Chainlit auth — generate with: chainlit create-secret
CHAINLIT_AUTH_SECRET=your-chainlit-secret

# Langfuse host (self-hosted default; set to https://cloud.langfuse.com for cloud)
LANGFUSE_HOST=http://localhost:3000
```

#### 3. Start the core Docker services

From the project root, ensure Docker Desktop is running, then:

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **ChromaDB** on port 8003

*Troubleshooting (Windows):* If you get IPv6 authentication errors, use `127.0.0.1` instead of `localhost` in your `DATABASE_URL`. Also ensure no native PostgreSQL Windows service is already occupying port 5432.

#### 4. Install Python dependencies

```bash
cd src
uv sync
```

Activate the virtual environment:

- **Mac/Linux:** `source .venv/bin/activate`
- **Windows:** `.\.venv\Scripts\activate`

#### 5. Apply the database schema

```bash
cd src/schema
uv run alembic upgrade head
```

`uv run` picks up the correct environment even without manual activation. If your `DATABASE_URL` is correct this will create all tables.

#### 6. Build the frontend

```bash
cd frontend
npm install
npm run build
```

This produces `frontend/dist/`, which FastAPI serves as static files at its root.

#### 7. Start the backend

From `src/`:

```bash
cd src
fastapi dev server.py --port 8001
```

Port 8001 is required — port 8000 is reserved for the vLLM inference server.

The application is now available at **http://localhost:8001**.

---

### vLLM Inference Server (requires NVIDIA GPU)

The project ships with a `docker-compose.models.yaml` that starts vLLM (OpenAI-compatible inference on port 8000) and Unsloth (Jupyter Lab for fine-tuning on port 8002).

Create a `.env` file in the project root (or export the variables) before starting:

```env
HF_TOKEN=your-huggingface-token
MODEL=Qwen/Qwen2.5-7B-Instruct   # or any HF model ID
PORT=8000
GPU_MEMORY_UTILIZATION=0.9
dtype=auto
```

Then:

```bash
docker-compose -f docker-compose.models.yaml up -d
```

- vLLM API: http://localhost:8000
- Unsloth Jupyter Lab: http://localhost:8002

---

### Unsloth Fine-Tuning Library

The project also contains a Docker container provided by Unsloth to provide GPU efficient fine-tuning. This is built off of a Jupyter Notebook but has an extremely intuitive UI for LoRA parameter management, exporting, and comparison.

This is mutually exclusive with vLLM since these both use the GPU's memory. You will need a valid HF Token to properly use this container. Another very important aspect of this is you must use **Qwen/Qwen2.5-7B-Instruct** to make the LoRA since this is used for inference (unless you change the model that you are using).

Furthermore, if you want to use the LoRA adapters that you create, you will need to make a HuggingFace collection (this was the only way to directly hold the LoRA and pull them collectively for vLLM). This can be easily done on HuggingFace by going to your profile and creating a new collection. All of our LoRA adapters that we have trained are at this URL `https://huggingface.co/api/collections/nateenglert04/gllm-lora-adapaters-69e30bddbcc2181a634a925f`.

You will need to change this URL inside `chainlit-app.py` to your newly created collection to properly take in the LoRAs. When first pulling these LoRA on the UI by selecting the profiles, the chat bot will not work immediately since it will need to pull the adapters (this only takes a couple seconds). 

### Langfuse Observability

Langfuse provides LLM tracing. The self-hosted stack lives in `langfuse_container/`.

```bash
cd langfuse_container
docker-compose up -d
```

Langfuse UI is at **http://localhost:3000**. Sign up, create a project, and copy your public/secret keys into the user settings within the gLLM dashboard to enable per-user tracing. Langfuse uses its own PostgreSQL on port 5433 to avoid conflicting with the app database.

To point the app at a different Langfuse instance (e.g., Langfuse Cloud), set `LANGFUSE_HOST` in `src/.env`:

```env
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

### Frontend Development Mode

For hot-reload frontend development, run the Vite dev server instead of building:

```bash
cd frontend
npm run dev
```

This starts at **http://localhost:5173** and proxies `/gllm`, `/admin`, `/chainlit-auth`, and `/assets` to the FastAPI backend on port 8001. The backend must already be running.

---

### Running Tests

Tests live in `tests/` and run against the `src` package. From `src/`:

```bash
uv run pytest
```

Tests marked `live` require the vLLM container to be running:

```bash
uv run pytest -m live
```
