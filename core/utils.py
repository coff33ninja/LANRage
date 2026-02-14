"""Utility functions for LANrage"""

import asyncio
import platform
import subprocess

from .logging_config import get_logger, timing_decorator

logger = get_logger(__name__)


@timing_decorator(name="check_admin_rights")
async def check_admin_rights() -> bool:
    """Check if running with admin/root privileges"""
    system = platform.system()

    if system == "Windows":
        try:
            import ctypes

            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            logger.debug(f"Admin rights check (Windows): {is_admin}")
            return is_admin
        except OSError as e:
            logger.warning(f"Failed to check admin rights on Windows: {e}")
            return False
        except AttributeError as e:
            logger.warning(f"Windows admin check not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking admin rights: {e}")
            return False
    else:
        # Unix-like systems
        import os

        is_admin = os.geteuid() == 0
        logger.debug(f"Admin rights check (Unix): {is_admin} (UID: {os.geteuid()})")
        return is_admin


@timing_decorator(name="run_elevated")
async def run_elevated(command: list[str]) -> subprocess.CompletedProcess:
    """Run a command with elevated privileges"""
    system = platform.system()
    logger.info(f"Running command with elevated privileges: {' '.join(command[:2])}...")

    if system == "Windows":
        # On Windows, we need to use PowerShell with Start-Process -Verb RunAs
        # This is complex, so for now we'll just fail with a helpful message
        logger.error("Admin rights required on Windows")
        raise PermissionError(
            "Admin rights required. Please run LANrage as Administrator."
        )
    # On Unix, use sudo
    if command[0] != "sudo":
        command = ["sudo"] + command

    logger.debug(f"Executing: {' '.join(command)}")
    proc = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode == 0:
        logger.debug("Command executed successfully")
    else:
        logger.warning(f"Command failed with return code {proc.returncode}")

    return subprocess.CompletedProcess(
        args=command,
        returncode=proc.returncode,
        stdout=stdout.decode("utf-8", errors="ignore"),
        stderr=stderr.decode("utf-8", errors="ignore"),
    )


def format_latency(latency_ms: float | None) -> str:
    """Format latency for display"""
    if latency_ms is None:
        return "N/A"

    if latency_ms < 10:
        return f"{latency_ms:.1f}ms ✓"
    if latency_ms < 30:
        return f"{latency_ms:.1f}ms ⚠"
    return f"{latency_ms:.1f}ms ✗"


def get_connection_emoji(connection_type: str) -> str:
    """Get emoji for connection type"""
    emojis = {
        "direct": "🔗",
        "relayed": "🔄",
        "connecting": "⏳",
        "host": "👑",
        "unknown": "❓",
    }
    return emojis.get(connection_type, "❓")


def calculate_latency(start_ms: float, end_ms: float) -> float:
    """Calculate latency between two timestamps.

    Args:
        start_ms: Start timestamp in milliseconds
        end_ms: End timestamp in milliseconds

    Returns:
        Latency in milliseconds
    """
    return end_ms - start_ms


def format_bandwidth(bytes_per_sec: float) -> str:
    """Format bandwidth for display.

    Args:
        bytes_per_sec: Bandwidth in bytes per second

    Returns:
        Formatted bandwidth string (e.g., "10.5 MB/s")
    """
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.1f} B/s"
    if bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    if bytes_per_sec < 1024 * 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"
    return f"{bytes_per_sec / (1024 * 1024 * 1024):.1f} GB/s"


def parse_port_range(port_range: str) -> list[int]:
    """Parse a port range string into a list of ports.

    Args:
        port_range: Port range string (e.g., "7777-7780" or "7777")

    Returns:
        List of port numbers

    Raises:
        ValueError: If port range is invalid
    """
    if "-" in port_range:
        start_str, end_str = port_range.split("-", 1)
        start = int(start_str.strip())
        end = int(end_str.strip())

        if start > end:
            raise ValueError(f"Invalid port range: {port_range} (start > end)")
        if start < 1 or end > 65535:
            raise ValueError(
                f"Invalid port range: {port_range} (ports must be 1-65535)"
            )

        return list(range(start, end + 1))
    port = int(port_range.strip())
    if port < 1 or port > 65535:
        raise ValueError(f"Invalid port: {port} (must be 1-65535)")
    return [port]
