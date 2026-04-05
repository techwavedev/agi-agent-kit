#!/usr/bin/env python3
"""
Path resolution module supporting dual-path logic (project-local + global).
Used by execution scripts to find directives, skills, and templates whether
the framework is installed in the current workspace or globally in ~/.agent.
"""

import os
from pathlib import Path


def get_global_root() -> Path:
    """Returns the global installation directory (~/.agent)."""
    return Path(os.path.expanduser("~/.agent"))


def get_project_root() -> Path:
    """Walk up from CWD to find the project root (has AGENTS.md or package.json)."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".agent").exists() or (parent / "AGENTS.md").exists() or (parent / "package.json").exists() or (parent / "directives" / "subagents").exists():
            return parent
    return current


def resolve_file(rel_path: str) -> Path:
    """
    Resolve a file path by checking project-local first, then global fallback.
    Returns the project-local path if neither exists, so error messages point there.
    """
    local_path = get_project_root() / rel_path
    if local_path.exists():
        return local_path
        
    global_path = get_global_root() / rel_path
    if global_path.exists():
        return global_path
        
    return local_path


def resolve_dir(rel_path: str) -> Path:
    """
    Resolve a directory path by checking project-local first, then global fallback.
    Returns the project-local path if neither exists.
    """
    return resolve_file(rel_path)

def gather_from_both(rel_path: str) -> list[Path]:
    """
    Yields all file paths matching within a directory from BOTH local and global.
    Local paths override global ones with the same relative name.
    """
    files = {}
    
    global_dir = get_global_root() / rel_path
    if global_dir.exists() and global_dir.is_dir():
        for f in global_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(global_dir)
                files[str(rel)] = f
                
    local_dir = get_project_root() / rel_path
    if local_dir.exists() and local_dir.is_dir():
        for f in local_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(local_dir)
                files[str(rel)] = f
                
    return list(files.values())
