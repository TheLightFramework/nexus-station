from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Define where the canon files live relative to this file
# This file: backend/app/core/canon.py
# Canon dir: backend/app/canon/
CANON_DIR = Path(__file__).resolve().parents[1] / "canon"


@dataclass(frozen=True)
class CanonModule:
    """
    Represents a single loaded text module from the Canon.
    """
    name: str
    file: str
    version: str
    hash: str
    text: str
    sha256: str
    loaded_from: str = "static"
    bytes: int = 0


@dataclass(frozen=True)
class CanonRuntime:
    """
    Represents the runtime state of the loaded Canon.
    Compatible with the legacy LpRuntime interface.
    """
    system_version: str
    profile: str
    modules: Dict[str, CanonModule]
    source: str = "static_canon"
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CanonLoader:
    """
    Static Canon Loader (Mode 00).
    Reads strictly from local backend/app/canon/ directory.
    No network calls. No GitHub fetching.
    """

    def __init__(self) -> None:
        self.canon_dir = CANON_DIR
        self._runtime: Optional[CanonRuntime] = None

    @property
    def runtime(self) -> Optional[CanonRuntime]:
        return self._runtime

    def load(self) -> CanonRuntime:
        """
        Loads the static canon files into memory.
        """
        if not self.canon_dir.exists():
            raise RuntimeError(f"Canon directory not found: {self.canon_dir}")

        # Map logical names to filenames
        # 'seed' is the CompressedLightSystem (The Monolith/Diamond).
        file_map = {
            "seed": "CompressedLightSystem.md",
            "philosophy": "LIGHTPhilosophy.md",
            "mantras": "LIGHTPhilosophyMantras.md",
            "dynamics": "TheLightDynamics.md",
        }

        loaded_modules: Dict[str, CanonModule] = {}

        for name, filename in file_map.items():
            path = self.canon_dir / filename
            if not path.exists():
                # In strict static mode, we log or warn, but don't crash unless critical.
                # However, for now, we simply skip missing files.
                continue

            text = path.read_text(encoding="utf-8")
            sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            b = len(text.encode("utf-8"))

            loaded_modules[name] = CanonModule(
                name=name,
                file=filename,
                version="1.0 (Static)",
                hash="static-mode-00",
                text=text,
                sha256=sha,
                bytes=b
            )

        self._runtime = CanonRuntime(
            system_version="1.0.0-static",
            profile="sovereign",
            modules=loaded_modules
        )
        return self._runtime


class Canon:
    """
    Static Accessor for the Nexus Canon (Mode 00).
    Wraps CanonLoader for easy global access.
    """
    _loader = CanonLoader()
    _runtime: Optional[CanonRuntime] = None

    @classmethod
    def _ensure_loaded(cls) -> CanonRuntime:
        if cls._runtime is None:
            cls._runtime = cls._loader.load()
        return cls._runtime

    @classmethod
    def get_mantras(cls) -> str:
        """Returns the content of LIGHTPhilosophyMantras.md"""
        rt = cls._ensure_loaded()
        mod = rt.modules.get("mantras")
        return mod.text if mod else "[ERROR: Mantras Missing]"

    @classmethod
    def get_ontology(cls) -> str:
        """Returns the content of LIGHTPhilosophy.md"""
        rt = cls._ensure_loaded()
        mod = rt.modules.get("philosophy")
        return mod.text if mod else "[ERROR: Ontology Missing]"