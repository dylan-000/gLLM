import os
import sys

# Add src to the python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.insert(0, src_path)

# Optionally load .env if it exists (for local dev with services running)
try:
    from dotenv import load_dotenv

    env_path = os.path.join(src_path, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass
