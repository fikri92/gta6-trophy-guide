#!/usr/bin/env python3
"""Pre-submission verification for the Leonida Legend entry.

Static checks only -- no browser, no server -- so it can run as the last gate
after the screenshots exist. Five groups:

  1. trophy data: 55 items, complete schema, guides inside the word bounds,
     citations well-formed, roadmap ordered, meta counts honest.
  2. official text: name/description/grade still byte-identical to the
     supplied list, and the trophy order unchanged.
  3. offline: nothing in index.html, app.js or style.css pulls a remote
     script, stylesheet, font, image, import, fetch or CSS url().
  4. budget: file and byte counts inside the submission caps.
  5. screenshots: 3-4 images, correct format, inside the pixel and byte caps,
     and no stray .jpg left behind.

    python3 tools/verify.py
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"
SHOTS = ROOT / "screenshots"

GUIDE_MIN_WORDS = 40
GUIDE_MAX_WORDS = 110
MAX_SHOT_BYTES = 262_144
MAX_LONG_EDGE = 1280
MIN_SHORT_EDGE = 480
APP_MAX_FILES = 993
APP_MAX_BYTES = 48 * 1024 * 1024
INDEX_MAX_BYTES = 1024 * 1024

PROBLEMS: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}{f' -- {detail}' if detail else ''}")
    if not ok:
        PROBLEMS.append(label)


def heading(text: str) -> None:
    print()
    print("=" * 74)
    print(text)
    print("=" * 74)


def load_baseline() -> dict[str, Any] | None:
    """The supplied list, from the competition kit or from git HEAD."""
    for candidate in (
        pathlib.Path("/root/workspace/makefun/tg/gta6-trophy-guide-01-kit/starter/app/data/trophies.json"),
        pathlib.Path("/workspace/makefun/tg/gta6-trophy-guide-01-kit/starter/app/data/trophies.json"),
    ):
        if candidate.is_file():
            print(f"      baseline: {candidate}")
            return json.loads(candidate.read_text(encoding="utf-8"))
    try:
        raw = subprocess.run(
            ["git", "-C", str(ROOT), "show", "HEAD:app/data/trophies.json"],
            capture_output=True, text=True, check=True,
        ).stdout
        print("      baseline: git HEAD")
        return json.loads(raw)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def check_data(doc: dict[str, Any]) -> list[dict[str, Any]]:
    heading("1. TROPHY DATA")
    items: list[dict[str, Any]] = doc["trophies"]

    check(len(items) == 55, "55 trophies", f"{len(items)} items")
    ids = [t["id"] for t in items]
    check(sorted(ids) == list(range(1, 56)), "ids run 1-55 with no gaps", f"{len(set(ids))} unique")

    guides = [t for t in items if isinstance(t.get("guide"), str) and t["guide"].strip()]
    check(len(guides) == 55, "every trophy has a written guide", f"{len(guides)}/55")

    words = [len(t["guide"].split()) for t in items]
    check(
        all(GUIDE_MIN_WORDS <= w <= GUIDE_MAX_WORDS for w in words),
        f"every guide is {GUIDE_MIN_WORDS}-{GUIDE_MAX_WORDS} words",
        f"{min(words)}-{max(words)} words, {sum(words)} total",
    )

    allowed = {"story", "collectibles", "activities", "online", "platinum"}
    bad_kind = [t["id"] for t in items if t.get("kind") not in allowed]
    check(not bad_kind, "kind values are valid", f"bad ids {bad_kind}" if bad_kind else "all valid")

    check(
        all(isinstance(t.get("stage"), int) and 1 <= t["stage"] <= 8 for t in items),
        "stage is an int in 1-8",
        f"{sorted({t['stage'] for t in items})}",
    )
    check(len({t["stage"] for t in items}) == 8, "all eight stages are used")
    check(all(isinstance(t.get("missable"), bool) for t in items), "missable is boolean")
    check(all(isinstance(t.get("hidden"), bool) for t in items), "hidden is boolean")
    check(
        all(("missable_note" in t) == t["missable"] for t in items),
        "missable notes exist exactly where the flag is set",
        f"{sum(1 for t in items if t['missable'])} notes",
    )

    src_ok = all(
        isinstance(t.get("sources"), list)
        and 1 <= len(t["sources"]) <= 3
        and all(
            isinstance(s.get("name"), str) and s["name"].strip()
            and isinstance(s.get("url"), str) and s["url"].startswith("https://")
            for s in t["sources"]
        )
        for t in items
    )
    check(src_ok, "sources: 1-3 named https objects each")
    total_sources = sum(len(t["sources"]) for t in items)
    hosts = sorted({re.match(r"https://([^/]+)", s["url"]).group(1) for t in items for s in t["sources"]})  # type: ignore[union-attr]
    print(f"      {total_sources} citations across {len(hosts)} hosts: {', '.join(hosts)}")

    guides_unique = len({t["guide"] for t in items})
    check(guides_unique == 55, "no guide is duplicated", f"{guides_unique} distinct")

    roadmap = doc.get("roadmap", [])
    check(len(roadmap) == 8 and [r["stage"] for r in roadmap] == list(range(1, 9)), "roadmap has 8 ordered stages")
    check(all(r.get("title") and r.get("detail") for r in roadmap), "every stage has a title and detail")

    meta = doc.get("meta", {})
    actual = sum(1 for t in items if t["missable"])
    check(meta.get("missable_count") == actual, "meta.missable_count matches the data", f"{meta.get('missable_count')} vs {actual}")
    check(isinstance(meta.get("source_note"), str) and len(meta["source_note"]) > 40, "meta.source_note present")
    return items


def check_official(items: list[dict[str, Any]], doc: dict[str, Any]) -> None:
    heading("2. OFFICIAL TEXT PRESERVED")
    baseline = load_baseline()
    if baseline is None:
        print("SKIP  no baseline copy of the supplied data found")
        return
    originals = {t["id"]: t for t in baseline["trophies"]}
    drift = [
        (t["id"], field)
        for t in items
        for field in ("name", "description", "grade")
        if originals.get(t["id"], {}).get(field) != t[field]
    ]
    check(not drift, "names/descriptions/grades identical to the supplied list",
          f"drift: {drift}" if drift else "55/55 byte-identical")
    check([t["id"] for t in items] == [t["id"] for t in baseline["trophies"]], "trophy order unchanged")
    check(baseline.get("game") == doc.get("game"), "game title unchanged", str(doc.get("game")))


def check_offline() -> None:
    heading("3. NO EXTERNAL LOADS")
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    css = (APP / "style.css").read_text(encoding="utf-8")

    scripts = re.findall(r"""<script[^>]*\bsrc=["']([^"']+)""", html)
    links = re.findall(r"""<link[^>]*\bhref=["']([^"']+)""", html)
    imports = re.findall(r"""^\s*(?:import|export)\s[^;]*?from\s+["']([^"']+)["']""", js, re.M)
    imports += re.findall(r"""\bimport\(\s*["']([^"']+)["']""", js)
    fetches = re.findall(r"""\bfetch\(\s*["']([^"']+)["']""", js)
    css_urls = re.findall(r"""url\(\s*["']?([^"')]+)""", css)
    data_uris = re.findall(r"data:[^\s\"')]+", html + js + css)

    def remote(refs: list[str]) -> list[str]:
        return [r for r in refs if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", r, re.I)]

    check(not remote(scripts), "no remote <script src>", str(scripts) or "none")
    check(not remote(links), "no remote <link href>", str(links) or "none")
    check(not remote(imports), "no remote import specifiers", str(imports) or "none")
    check(not remote(fetches), "fetch() only targets local files", str(fetches))
    check(not css_urls, "no CSS url() references", str(css_urls) or "none")
    check(not data_uris, "no data: URIs", f"{len(data_uris)} found")
    check(
        all(not r.startswith("/") for r in scripts + links),
        "script and link references are relative",
        str(scripts + links),
    )
    http_strings = [
        (name, match)
        for name, text in (("index.html", html), ("app.js", js), ("style.css", css))
        for match in re.findall(r"https?://[^\s\"'`)]+", text)
    ]
    check(not http_strings, "no http(s) strings in the app source", str(http_strings) or "none")

    # A citation URL may appear only in the data file, rendered as a plain
    # link: assert the app never puts one in an attribute that loads.
    loader_attrs = re.findall(r"""(?:src|href)\s*=\s*["'](https?:)?//""", html)
    check(not loader_attrs, "no absolute URL in a loading attribute", f"{len(loader_attrs)} found")


def check_budget() -> None:
    heading("4. APP BUDGET")
    entries = list(APP.rglob("*"))
    files = [p for p in entries if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    check(len(entries) <= APP_MAX_FILES, f"app/ holds at most {APP_MAX_FILES} entries", f"{len(entries)}")
    check(total <= APP_MAX_BYTES, "app/ stays under 48 MiB", f"{total} bytes")
    index = (APP / "index.html").stat().st_size
    check(index <= INDEX_MAX_BYTES, "index.html stays under 1 MiB", f"{index} bytes")
    for path in sorted(files):
        print(f"      {path.relative_to(ROOT)}  {path.stat().st_size} bytes")


def check_screenshots() -> None:
    heading("5. SCREENSHOTS")
    from PIL import Image

    shots = sorted(SHOTS.glob("*.png")) + sorted(SHOTS.glob("*.jpg"))
    check(3 <= len(shots) <= 4, "three or four screenshots", f"{len(shots)}")
    for shot in shots:
        size = shot.stat().st_size
        with Image.open(shot) as image:
            fmt, (w, h) = image.format, image.size
            image.verify()
        long_edge, short_edge = max(w, h), min(w, h)
        ok = (
            size <= MAX_SHOT_BYTES
            and long_edge <= MAX_LONG_EDGE
            and short_edge >= MIN_SHORT_EDGE
            and fmt in ("PNG", "JPEG")
        )
        check(
            ok,
            f"{shot.name} inside the caps",
            f"{fmt} {w}x{h} {size} bytes, long {long_edge} short {short_edge}",
        )
    stray = sorted(p.name for p in SHOTS.glob("*.jpg"))
    check(not stray, "no leftover .jpg screenshots", str(stray) or "none")


def main() -> int:
    doc = json.loads((APP / "data" / "trophies.json").read_text(encoding="utf-8"))
    items = check_data(doc)
    check_official(items, doc)
    check_offline()
    check_budget()
    check_screenshots()

    heading("RESULT")
    if PROBLEMS:
        print(f"{len(PROBLEMS)} FAILURES:")
        for label in PROBLEMS:
            print(f"  - {label}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
