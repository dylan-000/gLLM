import subprocess
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

COMPOSE_FILENAME = "docker-compose.models.yaml"
DOCKER_COMPOSE_FILE = os.path.join(ROOT_DIR, COMPOSE_FILENAME)

def get_image_for_service(service_name: str) -> str:
    """Helper to get the expected image prefix for a service."""
    if service_name == "vllm":
        return "vllm/vllm-openai"
    elif service_name == "unsloth":
        return "unsloth/unsloth"
    return ""

def get_container_status(service_name: str) -> bool:
    """Check if a specific service container is running."""
    image_prefix = get_image_for_service(service_name)
    if not image_prefix:
        return False
    
    try:
        # Use ancestor filter to find containers spawned from the given image (works for docker run and compose)
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", f"ancestor={image_prefix}"],
            capture_output=True,
            text=True,
            check=True
        )
        # If there's an ID returned, the container is running
        return bool(result.stdout.strip())
    except Exception as e:
        print(f"Error checking status for {service_name}: {e}")
        return False

def start_container(service_name: str) -> bool:
    """Start a specific docker compose service, ensuring the other is stopped."""
    # Enforce mutual exclusivity
    other_service = "unsloth" if service_name == "vllm" else "vllm"
    if get_container_status(other_service):
        print(f"Stopping {other_service} before starting {service_name}...")
        stop_container(other_service)
        
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
    """Stop a specific docker service using its container ID."""
    image_prefix = get_image_for_service(service_name)
    if not image_prefix:
        return False
        
    try:
        # Find the container ID
        result = subprocess.run(
            ["docker", "ps", "-q", "--filter", f"ancestor={image_prefix}"],
            capture_output=True,
            text=True,
            check=True
        )
        container_ids = result.stdout.strip().split()
        
        if not container_ids:
            print(f"No running container found for {service_name}")
            return True # Already stopped
            
        # Stop all matching containers
        for cid in container_ids:
            subprocess.run(["docker", "stop", cid], check=True)
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping {service_name}: {e}")
        return False
