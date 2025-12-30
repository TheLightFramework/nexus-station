from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

import httpx


_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class LoadedModule:
    name: str
    file: str
    version: str
    hash: str
    text: str
    sha256: str
    loaded_from: str  # "remote" | "cache"
    bytes: int


@dataclass(frozen=True)
class LpRuntime:
    system_version: str
    profile: str
    modules: Dict[str, LoadedModule]
    source: str  # "remote" | "cache"
    fetched_at: str  # ISO timestamp


class LpManager:
    """
    Live-Patch loader:
      - downloads Lp_versions.json from GitHub
      - downloads required module files for a chosen profile
      - caches everything locally
      - on network failure, falls back to cache
    """

    def __init__(
        self,
        versions_url: str,
        profile: str = "full_stack",
        cache_dir: str = ".lp_cache",
        timeout_seconds: float = 6.0,
    ) -> None:
        self.versions_url = versions_url
        self.profile = profile
        self.cache_dir = Path(cache_dir)
        self.timeout_seconds = timeout_seconds

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._runtime: Optional[LpRuntime] = None

    @property
    def runtime(self) -> Optional[LpRuntime]:
        return self._runtime

    def status_dict(self) -> Dict[str, Any]:
        if not self._runtime:
            return {
                "ok": False,
                "source": None,
                "profile": self.profile,
                "versions_url": self.versions_url,
                "error": "LpRuntime not loaded yet",
            }
        return {
            "ok": True,
            "source": self._runtime.source,
            "system_version": self._runtime.system_version,
            "profile": self._runtime.profile,
            "fetched_at": self._runtime.fetched_at,
            "modules": {
                k: {
                    "file": v.file,
                    "version": v.version,
                    "hash": v.hash,
                    "sha256": v.sha256,
                    "bytes": v.bytes,
                    "loaded_from": v.loaded_from,
                }
                for k, v in self._runtime.modules.items()
            },
        }

    async def load(self) -> LpRuntime:
        """
        Try remote first; if remote fails, use cache.
        """
        try:
            runtime = await self._load_from_remote()
            self._runtime = runtime
            return runtime
        except Exception:
            runtime = self._load_from_cache()
            self._runtime = runtime
            return runtime

    # ----------------------------
    # Remote path
    # ----------------------------

    async def _load_from_remote(self) -> LpRuntime:
        versions = await self._fetch_json(self.versions_url)

        system_version = str(versions.get("system_version", ""))
        modules_def: Dict[str, Any] = versions.get("modules", {}) or {}
        profiles: Dict[str, Any] = versions.get("profiles", {}) or {}

        if self.profile not in profiles:
            raise ValueError(f"Unknown Lp profile: {self.profile}")

        module_names = profiles[self.profile]
        if not isinstance(module_names, list) or not module_names:
            raise ValueError(f"Invalid profile list for {self.profile}")

        base_url = self._base_url_for_modules(self.versions_url)

        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            tasks = []
            for name in module_names:
                if name not in modules_def:
                    raise ValueError(f"Profile references unknown module: {name}")
                m = modules_def[name]
                tasks.append(self._download_one_module(client, base_url, name, m))
            loaded_modules_list = await asyncio.gather(*tasks)

        loaded_modules: Dict[str, LoadedModule] = {m.name: m for m in loaded_modules_list}

        fetched_at = datetime.now(timezone.utc).isoformat()
        runtime = LpRuntime(
            system_version=system_version,
            profile=self.profile,
            modules=loaded_modules,
            source="remote",
            fetched_at=fetched_at,
        )

        # Save cache + manifest after successful remote load
        self._write_cache_versions(versions)
        self._write_cache_manifest(runtime)

        return runtime

    async def _download_one_module(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        name: str,
        module_def: Dict[str, Any],
    ) -> LoadedModule:
        file = str(module_def.get("file", "")).strip()
        version = str(module_def.get("version", "")).strip()
        h = str(module_def.get("hash", "")).strip()

        if not file or not _SAFE_FILENAME_RE.match(file):
            raise ValueError(f"Unsafe or missing module file name: {file!r}")

        file_url = urljoin(base_url, file)
        text = await self._fetch_text(client, file_url)

        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        b = len(text.encode("utf-8"))

        # Cache per-module file
        self._write_cache_file(file, text)

        return LoadedModule(
            name=name,
            file=file,
            version=version,
            hash=h,
            text=text,
            sha256=sha,
            loaded_from="remote",
            bytes=b,
        )

    # ----------------------------
    # Cache path
    # ----------------------------

    def _load_from_cache(self) -> LpRuntime:
        versions_path = self.cache_dir / "Lp_versions.json"
        if not versions_path.exists():
            raise RuntimeError("Remote fetch failed and no cached Lp_versions.json is available")

        versions = json.loads(versions_path.read_text(encoding="utf-8"))
        system_version = str(versions.get("system_version", ""))
        modules_def: Dict[str, Any] = versions.get("modules", {}) or {}
        profiles: Dict[str, Any] = versions.get("profiles", {}) or {}

        if self.profile not in profiles:
            raise RuntimeError(f"Cached versions does not contain profile: {self.profile}")

        module_names = profiles[self.profile]
        loaded_modules: Dict[str, LoadedModule] = {}

        for name in module_names:
            m = modules_def.get(name)
            if not m:
                raise RuntimeError(f"Cached versions missing module def: {name}")

            file = str(m.get("file", "")).strip()
            version = str(m.get("version", "")).strip()
            h = str(m.get("hash", "")).strip()

            p = self.cache_dir / file
            if not p.exists():
                raise RuntimeError(f"Remote fetch failed and cached module missing: {file}")

            text = p.read_text(encoding="utf-8")
            sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            b = len(text.encode("utf-8"))

            loaded_modules[name] = LoadedModule(
                name=name,
                file=file,
                version=version,
                hash=h,
                text=text,
                sha256=sha,
                loaded_from="cache",
                bytes=b,
            )

        fetched_at = datetime.now(timezone.utc).isoformat()
        return LpRuntime(
            system_version=system_version,
            profile=self.profile,
            modules=loaded_modules,
            source="cache",
            fetched_at=fetched_at,
        )

    # ----------------------------
    # Helpers
    # ----------------------------

    async def _fetch_json(self, url: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            text = await self._fetch_text(client, url)
        return json.loads(text)

    async def _fetch_text(self, client: httpx.AsyncClient, url: str) -> str:
        # basic scheme guard
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

        r = await client.get(url, headers={"Accept": "text/plain, application/json"})
        r.raise_for_status()
        return r.text

    def _base_url_for_modules(self, versions_url: str) -> str:
        """
        If versions_url ends with '.../Lp_versions.json', module files are assumed next to it.
        """
        # remove last path segment and keep trailing slash
        if "/" not in versions_url:
            raise ValueError("Invalid versions_url")
        base = versions_url.rsplit("/", 1)[0] + "/"
        return base

    def _write_cache_versions(self, versions: Dict[str, Any]) -> None:
        p = self.cache_dir / "Lp_versions.json"
        p.write_text(json.dumps(versions, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_cache_manifest(self, runtime: LpRuntime) -> None:
        manifest = {
            "system_version": runtime.system_version,
            "profile": runtime.profile,
            "source": runtime.source,
            "fetched_at": runtime.fetched_at,
            "modules": {
                k: {
                    "file": v.file,
                    "version": v.version,
                    "hash": v.hash,
                    "sha256": v.sha256,
                    "bytes": v.bytes,
                    "loaded_from": v.loaded_from,
                }
                for k, v in runtime.modules.items()
            },
        }
        (self.cache_dir / "lp_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _write_cache_file(self, filename: str, text: str) -> None:
        # extra guard against traversal
        if not _SAFE_FILENAME_RE.match(filename):
            raise ValueError(f"Unsafe filename: {filename}")
        (self.cache_dir / filename).write_text(text, encoding="utf-8")


def env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v.strip() if v and v.strip() else default
