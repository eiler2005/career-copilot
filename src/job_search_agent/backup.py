"""Consistent SQLite snapshots and checksum-verified restore into a new directory."""

import shutil
import sqlite3
from pathlib import Path

from .core import Store, atomic_write, digest, encode, now, read_json, validate_home


def backup(store: Store, destination: Path) -> dict:
    destination = validate_home(destination)
    if (
        destination.exists()
        or destination.is_relative_to(store.home)
        or store.home.is_relative_to(destination)
    ):
        raise ValueError("Backup requires a new directory separate from the live workspace")
    destination.mkdir(parents=True, mode=0o700)
    with sqlite3.connect(destination / "journal.sqlite") as connection:
        store.db.backup(connection)
    for path in store.home.rglob("*"):
        relative = path.relative_to(store.home)
        if path.is_symlink():
            raise ValueError("Workspace symlinks cannot be backed up safely")
        if path.is_file() and relative.name not in {
            "journal.sqlite",
            "journal.sqlite-wal",
            "journal.sqlite-shm",
            ".lock",
        }:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    manifest = {
        str(p.relative_to(destination)): digest(p.read_bytes())
        for p in destination.rglob("*")
        if p.is_file()
    }
    result = {
        "created_at": now(),
        "files": manifest,
        "encrypted": False,
        "off_machine": False,
        "warning": "Local backup only; configure encrypted off-machine storage separately",
    }
    atomic_write(destination / "backup-manifest.json", encode(result))
    store.event(
        "backup_created", [], {"manifest_sha256": digest(result), "file_count": len(manifest)}
    )
    return {
        "files": len(manifest),
        "manifest_sha256": digest(result),
        "encrypted": False,
        "off_machine": False,
    }


def restore(snapshot: Path, destination: Path) -> dict:
    snapshot = snapshot.resolve()
    destination = validate_home(destination)
    if destination.exists():
        raise ValueError("Restore destination must not exist")
    manifest = read_json(snapshot / "backup-manifest.json")
    for relative, expected in manifest["files"].items():
        path = (snapshot / relative).resolve()
        if (
            not path.is_relative_to(snapshot)
            or not path.is_file()
            or digest(path.read_bytes()) != expected
        ):
            raise ValueError("Backup checksum or path validation failed; restore not started")
    if "journal.sqlite" not in manifest["files"] or "workspace.json" not in manifest["files"]:
        raise ValueError("Incomplete backup")
    destination.mkdir(parents=True, mode=0o700)
    for relative in manifest["files"]:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(snapshot / relative, target)
    with sqlite3.connect(destination / "journal.sqlite") as connection:
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Restored database integrity failure")
    return {"restored_files": len(manifest["files"]), "verified": True}
