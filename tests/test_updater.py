"""Tests for git-based self-update helpers."""

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from core.updater import UpdateError, UpdateManager


def _cp(
    stdout: str = "", returncode: int = 0, stderr: str = ""
) -> CompletedProcess[str]:
    return CompletedProcess(
        args=["git"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_get_status_unsupported_when_not_git_checkout(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nversion = '1.3.1'\n", encoding="utf-8")

    updater = UpdateManager(repo_dir=tmp_path)
    status = updater.get_status()

    assert status["supported"] is False
    assert status["update_available"] is False
    assert status["local_version"] == "1.3.1"


def test_get_status_reports_update_available(monkeypatch, tmp_path: Path):
    (tmp_path / ".git").mkdir()
    updater = UpdateManager(repo_dir=tmp_path)

    mapping: dict[tuple[str, ...], CompletedProcess[str]] = {
        ("rev-parse", "--abbrev-ref", "HEAD"): _cp("main\n"),
        ("fetch", "--quiet", "origin", "main"): _cp(""),
        ("rev-list", "--count", "HEAD..origin/main"): _cp("2\n"),
        ("rev-list", "--count", "origin/main..HEAD"): _cp("0\n"),
        ("status", "--porcelain"): _cp(""),
        ("rev-parse", "HEAD"): _cp("abc123\n"),
        ("rev-parse", "origin/main"): _cp("def456\n"),
    }

    monkeypatch.setattr(updater, "_run_git", lambda *args: mapping[tuple(args)])
    status = updater.get_status()

    assert status["supported"] is True
    assert status["update_available"] is True
    assert status["can_update"] is True
    assert status["behind_commits"] == 2
    assert status["ahead_commits"] == 0
    assert status["dirty_worktree"] is False


def test_apply_update_rejects_dirty_worktree(monkeypatch, tmp_path: Path):
    (tmp_path / ".git").mkdir()
    updater = UpdateManager(repo_dir=tmp_path)

    mapping: dict[tuple[str, ...], CompletedProcess[str]] = {
        ("rev-parse", "--abbrev-ref", "HEAD"): _cp("main\n"),
        ("fetch", "--quiet", "origin", "main"): _cp(""),
        ("rev-list", "--count", "HEAD..origin/main"): _cp("1\n"),
        ("rev-list", "--count", "origin/main..HEAD"): _cp("0\n"),
        ("status", "--porcelain"): _cp(" M static/index.html\n"),
        ("rev-parse", "HEAD"): _cp("abc123\n"),
        ("rev-parse", "origin/main"): _cp("def456\n"),
    }

    monkeypatch.setattr(updater, "_run_git", lambda *args: mapping[tuple(args)])

    with pytest.raises(UpdateError, match="uncommitted changes"):
        updater.apply_update()


def test_apply_update_noop_when_up_to_date(monkeypatch, tmp_path: Path):
    (tmp_path / ".git").mkdir()
    updater = UpdateManager(repo_dir=tmp_path)

    mapping: dict[tuple[str, ...], CompletedProcess[str]] = {
        ("rev-parse", "--abbrev-ref", "HEAD"): _cp("main\n"),
        ("fetch", "--quiet", "origin", "main"): _cp(""),
        ("rev-list", "--count", "HEAD..origin/main"): _cp("0\n"),
        ("rev-list", "--count", "origin/main..HEAD"): _cp("0\n"),
        ("status", "--porcelain"): _cp(""),
        ("rev-parse", "HEAD"): _cp("abc123\n"),
        ("rev-parse", "origin/main"): _cp("abc123\n"),
    }

    monkeypatch.setattr(updater, "_run_git", lambda *args: mapping[tuple(args)])
    result = updater.apply_update()

    assert result["updated"] is False
    assert result["restart_recommended"] is False
