"""Network management - WireGuard interface and routing"""

import asyncio
import base64
import platform
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

from .config import Config
from .logging_config import get_logger, set_context, timing_decorator

logger = get_logger(__name__)


class WireGuardError(Exception):
    """WireGuard-related errors"""

    pass


class NetworkManager:
    """Manages WireGuard interface and network stack"""

    def __init__(self, config: Config):
        self.config = config
        self.interface_name = config.interface_name
        self.private_key: bytes | None = None
        self.public_key: bytes | None = None
        self.private_key_b64: str | None = None
        self.public_key_b64: str | None = None
        self.is_windows = platform.system() == "Windows"
        self.is_linux = platform.system() == "Linux"
        self.interface_created = False

        # Log file for network operations
        self.log_file = Path(config.config_dir) / "network.log"

    async def _log(self, message: str):
        """Log network operations to file"""
        try:
            import aiofiles

            timestamp = asyncio.get_event_loop().time()
            log_entry = f"[{timestamp}] {message}\n"

            # Ensure log directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to log file asynchronously
            async with aiofiles.open(self.log_file, "a", encoding="utf-8") as f:
                await f.write(log_entry)
        except OSError as e:
            # Log to stderr if file logging fails (disk full, permissions, etc.)
            import sys

            print(
                f"Warning: Failed to write to log file {self.log_file}: {e}",
                file=sys.stderr,
            )
        except Exception as e:
            # Catch any other unexpected errors
            import sys

            print(f"Warning: Unexpected error in logging: {e}", file=sys.stderr)

    @timing_decorator(name="network_init")
    async def initialize(self):
        """Initialize network interface"""
        logger.info(f"Initializing network interface: {self.interface_name}")

        # Check if WireGuard is installed
        if not await self._check_wireguard():
            await self._log("WireGuard not found")
            raise WireGuardError(
                "WireGuard not found. Install from: https://www.wireguard.com/install/"
            )

        # Generate or load WireGuard keys
        await self._ensure_keys()
        await self._log(f"Keys loaded: {self.public_key_b64[:20]}...")

        # Create WireGuard interface (platform-specific)
        try:
            await self._create_interface()
            self.interface_created = True
            await self._log(f"Interface {self.interface_name} created successfully")
        except Exception as e:
            await self._log(f"Failed to create interface: {e}")
            raise WireGuardError(f"Failed to create interface: {e}") from e

    async def _check_wireguard(self) -> bool:
        """Check if WireGuard is installed"""
        try:
            if self.is_windows:
                # On Windows, check if wireguard.exe exists in PATH
                # Try running wireguard with any command - it returns 1 but that means it exists
                result = await self._run_command(
                    ["wireguard", "/help"], check=False, timeout=5.0
                )
                # wireguard.exe returns 1 for /help, but that means it's installed
                # If it's not found, we'll get FileNotFoundError
                return True
            # Check for wg command
            result = await self._run_command(["which", "wg"], check=False, timeout=5.0)
            return result.returncode == 0
        except TimeoutError:
            await self._log("WireGuard check timed out")
            return False
        except FileNotFoundError as e:
            await self._log(f"WireGuard check failed - command not found: {e}")
            return False
        except subprocess.CalledProcessError as e:
            await self._log(f"WireGuard check failed - command error: {e}")
            return False
        except Exception as e:
            await self._log(f"WireGuard check failed - unexpected error: {e}")
            return False

    async def _ensure_keys(self):
        """Generate or load WireGuard keypair"""
        private_key_path = self.config.keys_dir / "private.key"
        public_key_path = self.config.keys_dir / "public.key"

        if private_key_path.exists() and public_key_path.exists():
            # Load existing keys
            self.private_key = private_key_path.read_bytes()
            self.public_key = public_key_path.read_bytes()
        else:
            # Generate new keypair using WireGuard's method
            # WireGuard uses Curve25519 keys
            private_key = x25519.X25519PrivateKey.generate()
            public_key = private_key.public_key()

            self.private_key = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )

            self.public_key = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            # Save keys
            private_key_path.write_bytes(self.private_key)
            public_key_path.write_bytes(self.public_key)

            # Secure permissions (Unix only)
            if not self.is_windows:
                private_key_path.chmod(0o600)

        # Convert to base64 for WireGuard
        self.private_key_b64 = base64.b64encode(self.private_key).decode("ascii")
        self.public_key_b64 = base64.b64encode(self.public_key).decode("ascii")

    async def _create_interface(self):
        """Create WireGuard interface"""
        if self.is_windows:
            await self._create_interface_windows()
        elif self.is_linux:
            await self._create_interface_linux()
        else:
            platform_name = sys.platform
            await self._log(f"Unsupported platform: {platform_name}")
            raise WireGuardError(f"Unsupported platform: {platform_name}")

    async def _create_interface_windows(self):
        """Create or reuse WireGuard interface on Windows"""
        import aiofiles

        # On Windows, we need a config file for the WireGuard service
        config_path = self.config.config_dir / f"{self.interface_name}.conf"

        # Generate WireGuard config
        config_content = f"""[Interface]
PrivateKey = {self.private_key_b64}
Address = 10.66.0.1/16
ListenPort = 51820
"""

        # Always update the config file (in case keys changed)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(config_path, "w", encoding="utf-8") as f:
            await f.write(config_content)
        await self._log(f"Updated config file: {config_path}")

        # Check if tunnel service already exists
        service_name = f"WireGuardTunnel${self.interface_name}"
        try:
            check_result = await self._run_command(
                ["sc", "query", service_name], check=False, timeout=5.0
            )
            if check_result.returncode == 0:
                await self._log(
                    f"Tunnel service {service_name} already exists, reusing it"
                )
                # Service exists, no need to install
                return
        except Exception as e:
            await self._log(f"Service check failed (will try to install): {e}")

        # Service doesn't exist, install it
        await self._log(f"Installing new tunnel service: {service_name}")
        try:
            await self._run_command(
                ["wireguard", "/installtunnelservice", str(config_path)], timeout=30.0
            )
            await self._log(f"Tunnel installed successfully: {self.interface_name}")
        except TimeoutError as e:
            error_msg = "WireGuard tunnel installation timed out after 30 seconds"
            await self._log(error_msg)
            raise WireGuardError(
                f"Failed to create Windows interface: Installation timed out. "
                f"The tunnel service may already exist. Check Windows Services for '{service_name}'. "
                f"Or try manually: wireguard /installtunnelservice {config_path}"
            ) from e
        except subprocess.CalledProcessError as e:
            error_msg = (
                f"WireGuard tunnel installation failed with exit code {e.returncode}"
            )
            if e.stderr:
                error_msg += f"\nStderr: {e.stderr}"
            if e.stdout:
                error_msg += f"\nStdout: {e.stdout}"
            await self._log(error_msg)
            raise WireGuardError(f"Failed to create Windows interface: {e}") from None
        except Exception as e:
            await self._log(f"Unexpected error creating Windows interface: {e}")
            raise WireGuardError(f"Failed to create Windows interface: {e}") from e

    async def _create_interface_linux(self):
        """Create WireGuard interface on Linux"""
        # Check if we have root/sudo
        if not await self._check_root():
            raise WireGuardError(
                "Root/sudo required to create WireGuard interface"
            ) from None

        try:
            # Create interface
            await self._run_command(
                [
                    "sudo",
                    "ip",
                    "link",
                    "add",
                    "dev",
                    self.interface_name,
                    "type",
                    "wireguard",
                ]
            )

            # Set private key
            proc = await asyncio.create_subprocess_exec(
                "sudo",
                "wg",
                "set",
                self.interface_name,
                "private-key",
                "/dev/stdin",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate(input=self.private_key_b64.encode())

            # Assign IP address
            await self._run_command(
                [
                    "sudo",
                    "ip",
                    "address",
                    "add",
                    "dev",
                    self.interface_name,
                    "10.66.0.1/16",
                ]
            )

            # Set MTU (WireGuard overhead)
            await self._run_command(
                [
                    "sudo",
                    "ip",
                    "link",
                    "set",
                    "mtu",
                    "1420",
                    "up",
                    "dev",
                    self.interface_name,
                ]
            )

            # Bring interface up
            await self._run_command(
                ["sudo", "ip", "link", "set", "up", "dev", self.interface_name]
            )

        except Exception as e:
            # Cleanup on failure
            await self._cleanup_interface_linux()
            raise WireGuardError(f"Failed to create Linux interface: {e}") from e

    async def _check_root(self) -> bool:
        """Check if we have root/sudo access"""
        try:
            result = await self._run_command(["sudo", "-n", "true"], check=False)
            return result.returncode == 0
        except FileNotFoundError as e:
            await self._log(f"Sudo check failed - sudo not found: {e}")
            return False
        except subprocess.CalledProcessError as e:
            await self._log(f"Sudo check failed - command error: {e}")
            return False
        except Exception as e:
            await self._log(f"Sudo check failed - unexpected error: {e}")
            return False

    async def _cleanup_interface_linux(self):
        """Cleanup Linux interface on error"""
        try:
            await self._run_command(
                ["sudo", "ip", "link", "delete", "dev", self.interface_name],
                check=False,
            )
        except subprocess.CalledProcessError as e:
            await self._log(f"Interface cleanup failed (non-critical): {e}")
        except Exception as e:
            self._log(
                f"Interface cleanup failed with unexpected error (non-critical): {e}"
            )

    async def measure_latency(self, peer_ip: str) -> float:
        """Measure latency to peer (in ms)"""
        try:
            if self.is_windows:
                # Windows ping
                result = await self._run_command(
                    ["ping", "-n", "1", "-w", "1000", peer_ip], check=False
                )

                if result.returncode == 0:
                    # Parse output for time
                    output = result.stdout
                    if "time=" in output or "time<" in output:
                        # Extract time value
                        import re

                        match = re.search(r"time[<=](\d+)ms", output)
                        if match:
                            return float(match.group(1))
            else:
                # Linux ping
                result = await self._run_command(
                    ["ping", "-c", "1", "-W", "1", peer_ip], check=False
                )

                if result.returncode == 0:
                    # Parse output for time
                    output = result.stdout
                    import re

                    match = re.search(r"time=(\d+\.?\d*)", output)
                    if match:
                        return float(match.group(1))

            # If ping failed or couldn't parse, return None
            self._log(
                f"Latency measurement to {peer_ip} failed - peer unreachable or timeout"
            )
            return None

        except subprocess.CalledProcessError as e:
            self._log(f"Latency measurement to {peer_ip} failed - command error: {e}")
            return None
        except ValueError as e:
            self._log(f"Latency measurement to {peer_ip} failed - parsing error: {e}")
            return None
        except Exception as e:
            self._log(
                f"Latency measurement to {peer_ip} failed - unexpected error: {e}"
            )
            return None

    @timing_decorator(name="add_wg_peer")
    async def add_peer(
        self, peer_public_key: str, peer_endpoint: str | None, allowed_ips: list[str]
    ):
        """Add a WireGuard peer"""
        set_context(peer_id_val=peer_public_key[:16])
        logger.info(f"Adding WireGuard peer: {peer_endpoint} ({','.join(allowed_ips)})")

        if not self.interface_created:
            raise WireGuardError("Interface not created")

        try:
            cmd = ["sudo", "wg", "set", self.interface_name, "peer", peer_public_key]

            if peer_endpoint:
                cmd.extend(["endpoint", peer_endpoint])

            cmd.extend(["allowed-ips", ",".join(allowed_ips)])

            # Add persistent keepalive for NAT traversal
            cmd.extend(["persistent-keepalive", "25"])

            await self._run_command(cmd)
            logger.debug(f"WireGuard peer added successfully")

        except Exception as e:
            logger.error(f"Failed to add peer: {e}")
            raise WireGuardError(f"Failed to add peer: {e}") from e

    @timing_decorator(name="remove_wg_peer")
    async def remove_peer(self, peer_public_key: str):
        """Remove a WireGuard peer"""
        set_context(peer_id_val=peer_public_key[:16])
        logger.info(f"Removing WireGuard peer")

        if not self.interface_created:
            raise WireGuardError("Interface not created") from None

        try:
            await self._run_command(
                [
                    "sudo",
                    "wg",
                    "set",
                    self.interface_name,
                    "peer",
                    peer_public_key,
                    "remove",
                ]
            )
        except Exception as e:
            raise WireGuardError(f"Failed to remove peer: {e}") from e

    async def get_interface_status(self) -> dict:
        """Get WireGuard interface status"""
        if not self.interface_created:
            return {"status": "not_created"}

        try:
            result = await self._run_command(
                ["sudo", "wg", "show", self.interface_name]
            )

            return {
                "status": "active",
                "interface": self.interface_name,
                "public_key": self.public_key_b64,
                "output": result.stdout,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def cleanup(self):
        """Cleanup WireGuard interface"""
        if not self.interface_created:
            return

        try:
            if self.is_windows:
                # Remove tunnel service
                await self._run_command(
                    ["wireguard", "/uninstalltunnelservice", self.interface_name],
                    check=False,
                )
            elif self.is_linux:
                await self._cleanup_interface_linux()
        except subprocess.CalledProcessError as e:
            self._log(f"Cleanup failed (non-critical): {e}")
        except Exception as e:
            self._log(f"Cleanup failed with unexpected error (non-critical): {e}")

    async def _run_command(
        self, cmd: list[str], check: bool = True, timeout: float = 30.0
    ) -> subprocess.CompletedProcess:
        """Run a command asynchronously with timeout"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            # Kill the process if it times out
            try:
                proc.kill()
                await proc.wait()
            except Exception:
                pass
            raise subprocess.TimeoutExpired(cmd, timeout) from None

        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout.decode("utf-8", errors="ignore"),
            stderr=stderr.decode("utf-8", errors="ignore"),
        )

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr
            )

        return result
