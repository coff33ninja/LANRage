"""Safe self-update helpers for LANrage.

This module provides a git-based update check and update execution path
designed for local/self-hosted deployments.
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path
from typing import Any


class UpdateError(RuntimeError):
    """Raised when update operations fail."""


class UpdateManager:
    """Manage git-based update checks and pulls."""

    def __init__(
        self,
        repo_dir: Path | None = None,
        remote: str = "origin",
        branch: str = "main",
    ) -> None:
        self.repo_dir = repo_dir or Path(__file__).resolve().parent.parent
        self.remote = remote
        self.branch = branch

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a git command in the repository directory."""
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )

    def _read_local_version(self) -> str | None:
        """Read project version from pyproject.toml if available."""
        pyproject = self.repo_dir / "pyproject.toml"
        if not pyproject.exists():
            return None

        try:
            with pyproject.open("rb") as handle:
                parsed = tomllib.load(handle)
            return parsed.get("project", {}).get("version")
        except Exception:
            return None

    def get_status(self) -> dict[str, Any]:
        """Return update availability and repository health details."""
        git_dir = self.repo_dir / ".git"
        if not git_dir.exists():
            return {
                "supported": False,
                "update_available": False,
                "reason": "Repository is not a git checkout",
                "local_version": self._read_local_version(),
            }

        branch_proc = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        if branch_proc.returncode != 0:
            return {
                "supported": False,
                "update_available": False,
                "reason": branch_proc.stderr.strip()
                or "Unable to determine current branch",
                "local_version": self._read_local_version(),
            }

        current_branch = branch_proc.stdout.strip()
        target_ref = f"{self.remote}/{self.branch}"

        fetch_proc = self._run_git("fetch", "--quiet", self.remote, self.branch)
        if fetch_proc.returncode != 0:
            return {
                "supported": True,
                "update_available": False,
                "reason": fetch_proc.stderr.strip() or "Failed to fetch remote changes",
                "local_version": self._read_local_version(),
                "current_branch": current_branch,
                "target_branch": self.branch,
            }

        behind_proc = self._run_git("rev-list", "--count", f"HEAD..{target_ref}")
        ahead_proc = self._run_git("rev-list", "--count", f"{target_ref}..HEAD")
        dirty_proc = self._run_git("status", "--porcelain")
        local_sha_proc = self._run_git("rev-parse", "HEAD")
        remote_sha_proc = self._run_git("rev-parse", target_ref)

        if behind_proc.returncode != 0 or ahead_proc.returncode != 0:
            raise UpdateError("Failed to calculate repository divergence")

        behind = int((behind_proc.stdout or "0").strip() or "0")
        ahead = int((ahead_proc.stdout or "0").strip() or "0")
        dirty = bool((dirty_proc.stdout or "").strip())

        return {
            "supported": True,
            "update_available": behind > 0,
            "can_update": behind > 0
            and not dirty
            and ahead == 0
            and current_branch == self.branch,
            "local_version": self._read_local_version(),
            "current_branch": current_branch,
            "target_branch": self.branch,
            "behind_commits": behind,
            "ahead_commits": ahead,
            "dirty_worktree": dirty,
            "local_sha": (local_sha_proc.stdout or "").strip(),
            "remote_sha": (remote_sha_proc.stdout or "").strip(),
            "reason": None,
        }

    def apply_update(self) -> dict[str, Any]:
        """Apply updates via fast-forward pull when safe."""
        status = self.get_status()
        if not status.get("supported"):
            raise UpdateError(
                status.get("reason") or "Updates are not supported in this installation"
            )

        if not status.get("update_available"):
            return {
                "updated": False,
                "message": "Already up to date",
                "restart_recommended": False,
                "status": status,
            }

        if status.get("dirty_worktree"):
            raise UpdateError("Cannot update with local uncommitted changes")
        if status.get("ahead_commits", 0) > 0:
            raise UpdateError(
                "Cannot auto-update because local branch is ahead of remote"
            )
        if status.get("current_branch") != status.get("target_branch"):
            raise UpdateError(
                f"Cannot auto-update from branch {status.get('current_branch')} to {status.get('target_branch')}"
            )

        pull_proc = self._run_git("pull", "--ff-only", self.remote, self.branch)
        if pull_proc.returncode != 0:
            stderr = pull_proc.stderr.strip()
            stdout = pull_proc.stdout.strip()
            raise UpdateError(stderr or stdout or "git pull --ff-only failed")

        refreshed_status = self.get_status()
        return {
            "updated": True,
            "message": "Update applied successfully",
            "restart_recommended": True,
            "status": refreshed_status,
        }
