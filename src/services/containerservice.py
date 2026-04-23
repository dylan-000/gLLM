import subprocess
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# If MOCK_CONTAINERS is set, use the lightweight alpine setup
if os.getenv("MOCK_CONTAINERS", "false").lower() == "true":
    COMPOSE_FILENAME = "docker-compose.mock.yaml"
else:
    COMPOSE_FILENAME = "docker-compose.models.yaml"

DOCKER_COMPOSE_FILE = os.path.join(ROOT_DIR, COMPOSE_FILENAME)

def get_container_status(service_name: str) -> bool:
    """Check if a specific docker compose service is running."""
    try:
        result = subprocess.run(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "ps", "--services", "--filter", "status=running"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False
        )
        running_services = result.stdout.strip().split("\n")
        return service_name in running_services
    except Exception as e:
        print(f"Error checking status for {service_name}: {e}")
        return False

def start_container(service_name: str) -> bool:
    """Start a specific docker compose service."""
    try:
        subprocess.run(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d", service_name],
            cwd=ROOT_DIR,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error starting {service_name}: {e}")
        return False

def stop_container(service_name: str) -> bool:
    """Stop a specific docker compose service."""
    try:
        subprocess.run(
            ["docker-compose", "-f", DOCKER_COMPOSE_FILE, "stop", service_name],
            cwd=ROOT_DIR,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping {service_name}: {e}")
        return False
