"""Port utility functions for checking port availability"""
import socket
import random
import logging

logger = logging.getLogger(__name__)


def is_port_available(host: str, port: int) -> bool:
    """
    Check if a port is available
    
    Args:
        host: Host address
        port: Port number
    
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # 0 means port is in use
    except Exception as e:
        logger.warning(f"Error checking port {port}: {e}")
        return False


def find_available_port(host: str, preferred_port: int, max_attempts: int = 100) -> int:
    """
    Find an available port, starting with preferred port
    
    Args:
        host: Host address
        preferred_port: Preferred port number
        max_attempts: Maximum attempts to find available port
    
    Returns:
        Available port number
    """
    # First try preferred port
    if is_port_available(host, preferred_port):
        logger.info(f"Preferred port {preferred_port} is available")
        return preferred_port
    
    logger.warning(f"Preferred port {preferred_port} is in use, searching for alternative...")
    
    # Try random ports in a reasonable range (49152-65535 for dynamic/private ports)
    for _ in range(max_attempts):
        # Use a range that's less likely to conflict
        random_port = random.randint(49152, 65535)
        if is_port_available(host, random_port):
            logger.info(f"Found available port: {random_port}")
            return random_port
    
    # If no port found, raise exception
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

