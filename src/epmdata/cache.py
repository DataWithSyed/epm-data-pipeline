"""HTTP fetch with on-disk cache. Raw blobs stay in data/raw (git-ignored)."""
from __future__ import annotations

import time
from pathlib import Path

import requests

from epmdata.paths import USER_AGENT


def get(
    url: str,
    dest: Path,
    *,
    refresh: bool = False,
    binary: bool = False,
    timeout: int = 120,
    max_attempts: int = 5,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not refresh:
        return dest
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 15))
                time.sleep(wait)
                continue
            if r.status_code >= 500 and attempt < max_attempts - 1:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            if binary:
                dest.write_bytes(r.content)
            else:
                dest.write_text(r.text, encoding="utf-8")
            return dest
        except Exception as exc:  # noqa: BLE001 — surface after retries
            last_err = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Download failed after {max_attempts} attempts: {url}") from last_err
