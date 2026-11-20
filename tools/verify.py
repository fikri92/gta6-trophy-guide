#!/usr/bin/env python3
"""Pre-submission verification for the GTA VI trophy guide entry.

Checks (each printed with its real values, never assumed):
  1. app/data/trophies.json parses, 55 items, every required key present and valid
  2. official name/description text is byte-identical to the supplied list
  3. no external loads: script src / link href / import specifiers / fetch() / CSS url()
  4. app/ file and byte budget
  5. screenshots: image type, dimensions, byte cap
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP = ROOT / "app"
PROBLEMS: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not ok:
        PROBLEMS.append(label)


def main() -> int:
    doc = json.loads((APP / "data" / "trophies.json").read_text(encoding="utf-8"))
    items = doc["trophies"]
    print("=" * 78)
    print("1. TROPHY DATA")
    print("=" * 78)
    check(len(items) == 55, "55 trophies", f"{len(items)} items")
    check(len({t["id"] for t in items}) == 55, "unique ids", f"max id {max(t['id'] for t in items)}")

    guides = [t for t in items if isinstance(t.get("guide"), str) and t["guide"].strip()]
    check(len(guides) == 55, "every trophy has a non-blank guide", f"{len(guides)}/55")
    words = [len(t["guide"].split()) for t in items]
    check(all(40 <= w <= 110 for w in words), "every guide is 40-110 words", f"{min(words)}-{max(words)} words")

    for key, allowed in (("kind", {"story", "collectibles", "activities", "online", "platinum"}),):
        bad = [t["id"] for t in items if t.get(key) not in allowed]
        check(not bad, f"{key} values valid", f"bad ids {bad}" if bad else "all valid")
    check(all(isinstance(t.get("stage"), int) and 1 <= t["stage"] <= 8 for t in items), "stage is an int 1-8")
    check(len({t["stage"] for t in items}) == 8, "all 8 stages used", f"{sorted({t['stage'] for t in items})}")
    check(all(isinstance(t.get("missable"), bool) for t in items), "missable is boolean")
    check(all(isinstance(t.get("hidden"), bool) for t in items), "hidden is boolean")

    src_ok = all(
        isinstance(t.get("sources"), list) and 1 <= len(t["sources"]) <= 3 and all(isinstance(s.get("name"), str) and s["name"].strip() and isinstance(s.get("url"), str) and s["url"].startswith("https://") for s in t["sources"])
        for t in items
    )
    check(src_ok, "sources: 1-3 named https objects each")
    total_sources = sum(len(t["sources"]) for t in items)
    hosts = sorted({re.match(r"https://([^/]+)", s["url"]).group(1) for t in items for s in t["sources"]})
    print(f"      {total_sources} source citations across {len(hosts)} hosts: {', '.join(hosts)}")

    roadmap = doc.get("roadmap", [])
    check(len(roadmap) == 8 and [r["stage"] for r in roadmap] == list(range(1, 9)), "roadmap has 8 ordered stages")
    check(all(r.get("title") and r.get("detail") for r in roadmap), "roadmap entries have title + detail")
    meta = doc.get("meta", {})
    check(meta.get("missable_count") == sum(1 for t in items if t["missable"]), "meta.missable_count matches data", str(meta.get("missable_count")))
    check(isinstance(meta.get("source_note"), str) and len(meta["source_note"]) > 40, "meta.source_note present")

    print()
    print("=" * 78)
    print("2. OFFICIAL TEXT PRESERVED")
    print("=" * 78)
    # Baseline: the supplied starter data, from the competition kit or a git baseline if one exists.
    import subprocess

    baseline = None
    for candidate in (
        pathlib.Path("/root/workspace/makefun/tg/gta6-trophy-guide-01-kit/starter/app/data/trophies.json"),
        pathlib.Path("/workspace/makefun/tg/gta6-trophy-guide-01-kit/starter/app/data/trophies.json"),
    ):
        if candidate.is_file():
            baseline = json.loads(candidate.read_text(encoding="utf-8"))
            print(f"      baseline: {candidate}")
            break
    if baseline is None:
        try:
            baseline = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:app/data/trophies.json"], capture_output=True, text=True, check=True).stdout)
            print("      baseline: git HEAD")
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass

    if baseline is None:
        print("SKIP  no baseline copy of the supplied data found")
    else:
        o_by_id = {t["id"]: t for t in baseline["trophies"]}
        drift = [(t["id"], f) for t in items for f in ("name", "description", "grade") if o_by_id[t["id"]][f] != t[f]]
        check(not drift, "names/descriptions/grades identical to the supplied list", f"drift: {drift}" if drift else "55/55 byte-identical")
        check([t["id"] for t in items] == [t["id"] for t in baseline["trophies"]], "trophy order unchanged")
        check(baseline.get("game") == doc.get("game"), "game title unchanged", str(doc.get("game")))

    print()
    print("=" * 78)
    print("3. NO EXTERNAL LOADS")
    print("=" * 78)
    html = (APP / "index.html").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")
    css = (APP / "style.css").read_text(encoding="utf-8")

    bad_scripts = re.findall(r"<script[^>]*\bsrc=[\"']([^\"']+)", html)
    bad_links = re.findall(r"<link[^>]*\bhref=[\"']([^\"']+)", html)
    imports = re.findall(r"""^\s*(?:import|export)\s[^;]*?from\s+[\"']([^\"']+)[\"']""", js, re.M) + re.findall(r"""\bimport\(\s*[\"']([^\"']+)[\"']""", js)
    fetches = re.findall(r"""\bfetch\(\s*[\"']([^\"']+)[\"']""", js)
    css_urls = re.findall(r"""url\(\s*[\"']?([^\"')]+)""", css)
    data_urls = re.findall(r"data:[^\s\"')]+", html + js + css)

    def external(refs: list[str]) -> list[str]:
        return [r for r in refs if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", r, re.I)]

    check(not external(bad_scripts), "no remote <script src>", str(bad_scripts))
    check(not external(bad_links), "no remote <link href>", str(bad_links))
    check(not external(imports), "no remote import specifiers", str(imports) or "none")
    check(not external(fetches), "fetch() targets are local", str(fetches))
    check(not css_urls, "no CSS url() references", str(css_urls) or "none")
    check(not data_urls, "no data: URIs", f"{len(data_urls)} found")
    check(all(not r.startswith("/") for r in bad_scripts + bad_links), "references are relative (no leading /)")
    http_strings = [(f, m) for f, text in (("index.html", html), ("app.js", js), ("style.css", css)) for m in re.findall(r"https?://[^\s\"'`)]+", text)]
    check(not http_strings, "no http(s) strings in app source", str(http_strings) or "none")

    print()
    print("=" * 78)
    print("4. APP BUDGET")
    print("=" * 78)
    entries = [p for p in APP.rglob("*")]
    files = [p for p in entries if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    check(len(entries) <= 993, "app/ entries <= 993", f"{len(entries)}")
    check(total <= 48 * 1024 * 1024, "app/ bytes <= 48 MiB", f"{total} bytes")
    idx = (APP / "index.html").stat().st_size
    check(idx <= 1024 * 1024, "index.html <= 1 MiB", f"{idx} bytes")
    for p in sorted(files):
        print(f"      {p.relative_to(ROOT)}  {p.stat().st_size} bytes")

    print()
    print("=" * 78)
    print("5. SCREENSHOTS")
    print("=" * 78)
    from PIL import Image

    shots = sorted((ROOT / "screenshots").glob("*.png")) + sorted((ROOT / "screenshots").glob("*.jpg"))
    check(3 <= len(shots) <= 4, "3 or 4 screenshots", f"{len(shots)}")
    for s in shots:
        size = s.stat().st_size
        with Image.open(s) as im:
            fmt, (w, h) = im.format, im.size
            im.verify()
        long_side, short_side = max(w, h), min(w, h)
        ok = size <= 262144 and long_side <= 1280 and short_side >= 480 and fmt in ("PNG", "JPEG")
        check(ok, f"{s.name} valid image within caps", f"{fmt} {w}x{h} {size} bytes")
    stale = list((ROOT / "screenshots").glob("*.jpg"))
    check(not stale, "no leftover .jpg screenshots", str([s.name for s in stale]) or "none")

    print()
    print("=" * 78)
    print("RESULT:", "ALL CHECKS PASSED" if not PROBLEMS else f"{len(PROBLEMS)} FAILURES: {PROBLEMS}")
    print("=" * 78)
    return 0 if not PROBLEMS else 1


if __name__ == "__main__":
    sys.exit(main())
