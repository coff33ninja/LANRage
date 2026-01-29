"""Utility functions for LANrage"""

import asyncio
import platform
import subprocess
import sys
from typing import Optional


async def check_admin_rights() -> bool:
    """Check if running with admin/root privileges"""
    system = platform.system()

    if system == "Windows":
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except OSError as e:
            # Log Windows API errors
            print(
                f"Warning: Failed to check admin rights on Windows: {e}",
                file=sys.stderr,
            )
            return False
        except AttributeError as e:
            # Log if windll or shell32 not available
            print(f"Warning: Windows admin check not available: {e}", file=sys.stderr)
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(
                f"Warning: Unexpected error checking admin rights: {e}", file=sys.stderr
            )
            return False
    else:
        # Unix-like systems
        import os

        return os.geteuid() == 0


async def run_elevated(command: list[str]) -> subprocess.CompletedProcess:
    """Run a command with elevated privileges"""
    system = platform.system()

    if system == "Windows":
        # On Windows, we need to use PowerShell with Start-Process -Verb RunAs
        # This is complex, so for now we'll just fail with a helpful message
        raise PermissionError(
            "Admin rights required. Please run LANrage as Administrator."
        )
    else:
        # On Unix, use sudo
        if not command[0] == "sudo":
            command = ["sudo"] + command

        proc = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        return subprocess.CompletedProcess(
            args=command,
            returncode=proc.returncode,
            stdout=stdout.decode("utf-8", errors="ignore"),
            stderr=stderr.decode("utf-8", errors="ignore"),
        )


def format_latency(latency_ms: Optional[float]) -> str:
    """Format latency for display"""
    if latency_ms is None:
        return "N/A"

    if latency_ms < 10:
        return f"{latency_ms:.1f}ms ✓"
    elif latency_ms < 30:
        return f"{latency_ms:.1f}ms ⚠"
    else:
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
