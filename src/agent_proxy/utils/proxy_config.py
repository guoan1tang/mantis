"""macOS system proxy auto-configuration."""
from __future__ import annotations

import subprocess
import logging

logger = logging.getLogger(__name__)


def _get_active_service() -> str | None:
    """Get the active network service name."""
    try:
        # Try -listnetworkserviceorder to find the first enabled service
        result = subprocess.run(
            ["networksetup", "-listnetworkserviceorder"],
            capture_output=True, text=True, timeout=5,
        )
        # Parse: look for first enabled service (hardwareport has a non-null value)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("(Hardware Port:"):
                # Extract service name: (Hardware Port: Wi-Fi, Device: en0)
                name = line.split("Hardware Port:")[1].split(",")[0].strip()
                return name
    except (subprocess.SubprocessError, FileNotFoundError, IndexError):
        pass

    # Fallback: check Wi-Fi is enabled
    try:
        result = subprocess.run(
            ["networksetup", "-getinfo", "Wi-Fi"],
            capture_output=True, text=True, timeout=5,
        )
        if "IP address:" in result.stdout:
            return "Wi-Fi"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return None


def set_system_proxy(host: str, port: int) -> bool:
    """Set macOS system HTTP/HTTPS proxy."""
    service = _get_active_service()
    if not service:
        logger.error("No active network service found for proxy configuration")
        return False

    try:
        subprocess.run(
            ["networksetup", "-setwebproxy", service, host, str(port)],
            capture_output=True, timeout=5, check=True,
        )
        subprocess.run(
            ["networksetup", "-setwebproxystate", service, "on"],
            capture_output=True, timeout=5, check=True,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxy", service, host, str(port)],
            capture_output=True, timeout=5, check=True,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxystate", service, "on"],
            capture_output=True, timeout=5, check=True,
        )
        logger.info(f"System proxy set to {host}:{port} on {service}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to set system proxy: {e}")
        return False


def clear_system_proxy() -> bool:
    """Clear macOS system proxy."""
    service = _get_active_service()
    if not service:
        return False

    try:
        subprocess.run(
            ["networksetup", "-setwebproxystate", service, "off"],
            capture_output=True, timeout=5, check=True,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxystate", service, "off"],
            capture_output=True, timeout=5, check=True,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to clear system proxy: {e}")
        return False
