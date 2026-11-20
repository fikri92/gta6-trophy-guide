#!/usr/bin/env python3
"""Capture the four submission screenshots.

Framing is decided by measurement, not by eye:

  * every frame edge lands in a gap between cards, never across one, so no
    card is sliced in half;
  * the cover keeps the sticky header, the four grade tallies and at least
    two whole cards in view, at the standard 1280x800 viewport;
  * the roadmap holds all eight stages in one frame, captured on a taller
    viewport so the text stays at full size instead of being zoomed down;
  * the toast is suppressed, so nothing floats over a card;
  * every PNG ends under 200 KiB, with 256 KiB as the hard cap and 1280 px
    as the long-edge limit.

Needs `node serve.ts` running on port 8080.

    python3 tools/screenshots.py
"""

from __future__ import annotations

import pathlib
import sys

from PIL import Image
from playwright.sync_api import Page, sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
BASE = "http://localhost:8080/"

WIDTH, HEIGHT = 1280, 800
LONG_EDGE_CAP = 1280
SHORT_EDGE_MIN = 480
MAX_BYTES = 262_144
SAFE_BYTES = 200 * 1024

# A realistic session: the early trophies plus several side-strand earns, so
# the header, the tallies and the cards all show mixed state.
EARNED = [2, 3, 4, 5, 8, 9, 10, 21, 44, 46, 51, 22, 23, 24]

TOAST_OFF = "#toast{display:none !important}"


def hide_toast(page: Page) -> None:
    """The toast is a transient overlay; no screenshot should carry it."""
    page.evaluate("document.getElementById('toast').classList.remove('is-visible')")
    page.add_style_tag(content=TOAST_OFF)


def boxes(page: Page, selector: str) -> list[tuple[float, float]]:
    """Top and bottom of every match, in viewport coordinates."""
    return page.evaluate(
        """(sel) => [...document.querySelectorAll(sel)].map(el => {
            const r = el.getBoundingClientRect();
            return [r.top, r.bottom];
        })""",
        selector,
    )


def cut_at(page: Page, selector: str, edge: float) -> list[tuple[int, int]]:
    """Elements the horizontal line `edge` would slice through."""
    return [
        (round(top), round(bottom))
        for top, bottom in boxes(page, selector)
        if top < edge < bottom
    ]


def align_bottom_edge(page: Page, selector: str, height: int, base_scroll: int | None = None) -> int:
    """Scroll a few pixels until y=height falls in a gap, not through a card.

    Only downward micro-adjustments are allowed, so the shot keeps the
    composition it was framed for. Returns the scroll offset used.
    """
    if base_scroll is not None:
        page.evaluate(f"window.scrollTo(0, {base_scroll})")
        page.wait_for_timeout(280)
    start = int(page.evaluate("window.scrollY"))
    for delta in range(0, 180, 4):
        page.evaluate(f"window.scrollTo(0, {start + delta})")
        page.wait_for_timeout(60)
        if not cut_at(page, selector, height):
            return start + delta
    raise SystemExit(f"no scroll position puts the {height}px edge in a gap below y={start}")


def report_edges(page: Page, selector: str, height: int, label: str) -> int:
    """Assert the outer frame edges are clean and count whole elements."""
    sliced = cut_at(page, selector, height)
    if sliced:
        raise SystemExit(f"{label}: the {height}px edge slices {len(sliced)} element(s): {sliced}")
    whole = sum(1 for top, bottom in boxes(page, selector) if 0 <= top and bottom <= height)
    return whole


def compress(path: pathlib.Path) -> tuple[int, int, tuple[int, int]]:
    """Keep the capture under the byte cap, quantising only if it must."""
    with Image.open(path) as image:
        width, height = image.size
    if max(width, height) > LONG_EDGE_CAP:
        with Image.open(path) as image:
            scale = LONG_EDGE_CAP / max(image.size)
            image.convert("RGB").resize(
                (round(width * scale), round(height * scale)), Image.LANCZOS
            ).save(path, "PNG", optimize=True)

    size = path.stat().st_size
    if size <= SAFE_BYTES:
        with Image.open(path) as image:
            return size, 256, image.size

    with Image.open(path) as image:
        source = image.convert("RGB")
    staging = path.with_suffix(".tmp")
    for colours in (256, 192, 128, 96):
        source.quantize(colors=colours, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG).save(
            staging, "PNG", optimize=True
        )
        if staging.stat().st_size <= SAFE_BYTES:
            staging.replace(path)
            with Image.open(path) as image:
                return path.stat().st_size, colours, image.size
        staging.unlink()
    raise SystemExit(f"{path.name} cannot be compressed under {SAFE_BYTES} bytes")


def main() -> int:
    SHOTS.mkdir(exist_ok=True)
    for stale in [*SHOTS.glob("*.jpg"), *SHOTS.glob("*.jpeg")]:
        stale.unlink()
        print(f"removed stale {stale.name}")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
        page.goto(BASE, wait_until="load")
        page.wait_for_selector(".card")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_selector(".card")

        for tid in EARNED:
            page.locator(f'.card[data-id="{tid}"] .check').click()
        page.wait_for_timeout(420)
        hide_toast(page)
        print(
            "session:",
            page.locator("#earned-count").inner_text(),
            page.locator("#pct").inner_text(),
            "|",
            page.locator("#missable-left").inner_text(),
        )

        header_bottom = int(page.evaluate("document.querySelector('.topbar').getBoundingClientRect().bottom"))
        tallies = int(page.evaluate("document.querySelectorAll('#stats .gcell').length"))

        # -- 1. cover ------------------------------------------------------
        # Top of the page at the standard viewport: the header and tallies
        # are in shot, then cards. A few pixels of scroll put the bottom edge
        # in a gap so the third card is not sliced.
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(320)
        align_bottom_edge(page, ".card", HEIGHT)
        whole = report_edges(page, ".card", HEIGHT, "cover")
        print(f"cover: {WIDTH}x{HEIGHT}, header {header_bottom}px, {tallies} tallies, {whole} whole cards")
        if whole < 2:
            raise SystemExit("the cover must show at least two whole cards")
        page.screenshot(path=str(SHOTS / "1-cover.png"))

        # -- 2. checklist --------------------------------------------------
        # Mid-list: a story card with its guide and citations, both edges in
        # gaps.
        page.evaluate("""() => {
            const card = document.querySelector('.card[data-id="8"]');
            card.scrollIntoView({block: 'start'});
        }""")
        page.wait_for_timeout(340)
        page.evaluate("window.scrollBy(0, -96)")
        page.wait_for_timeout(280)
        align_bottom_edge(page, ".card", HEIGHT)
        whole = report_edges(page, ".card", HEIGHT, "checklist")
        print(f"checklist: {WIDTH}x{HEIGHT}, {whole} whole cards in frame")
        page.screenshot(path=str(SHOTS / "2-checklist.png"))

        # -- 3. roadmap ----------------------------------------------------
        # All eight stages must be in one frame. At 1280x800 the roadmap runs
        # to about 1120px, so the capture viewport grows instead of the page
        # shrinking: full-size text, and the long edge still lands on 1280.
        page.locator("#tab-roadmap").click()
        page.wait_for_timeout(380)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(280)
        stage_bottom = int(page.evaluate(
            "[...document.querySelectorAll('.stage')].pop().getBoundingClientRect().bottom"
        ))
        needed = max(stage_bottom + 16, HEIGHT)
        if needed > LONG_EDGE_CAP:
            raise SystemExit(f"the roadmap needs {needed}px, past the long-edge cap")
        page.set_viewport_size({"width": WIDTH, "height": needed})
        page.wait_for_timeout(460)
        stage_bottom = int(page.evaluate(
            "[...document.querySelectorAll('.stage')].pop().getBoundingClientRect().bottom"
        ))
        stages = int(page.evaluate("document.querySelectorAll('.stage').length"))
        chips = int(page.evaluate("document.querySelectorAll('.tchip').length"))
        print(f"roadmap: {stages} stages, {chips} chips, stage 8 ends at {stage_bottom}px of {needed}")
        if stages != 8:
            raise SystemExit(f"the roadmap frame must hold all eight stages, found {stages}")
        if chips != 55:
            raise SystemExit(f"the roadmap frame must place all 55 trophies, found {chips}")
        if stage_bottom > needed:
            raise SystemExit(f"stage 8 ends at {stage_bottom}px, outside the {needed}px frame")
        page.screenshot(path=str(SHOTS / "3-roadmap.png"))
        page.set_viewport_size({"width": WIDTH, "height": HEIGHT})
        page.wait_for_timeout(300)

        # -- 4. missable ---------------------------------------------------
        page.locator("#tab-missable").click()
        page.wait_for_timeout(380)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(320)
        align_bottom_edge(page, ".missable-card", HEIGHT)
        whole = report_edges(page, ".missable-card", HEIGHT, "missable")
        entries = int(page.evaluate("document.querySelectorAll('.missable-card').length"))
        print(f"missable: {entries} entries registered, {WIDTH}x{HEIGHT}, {whole} whole in frame")
        if whole < 4:
            raise SystemExit("the missable frame should show at least four whole entries")
        page.screenshot(path=str(SHOTS / "4-missable.png"))
        browser.close()

    print()
    ok = True
    for name in ("1-cover.png", "2-checklist.png", "3-roadmap.png", "4-missable.png"):
        path = SHOTS / name
        size, colours, (width, height) = compress(path)
        with Image.open(path) as image:
            image.verify()
        long_edge, short_edge = max(width, height), min(width, height)
        within = size < MAX_BYTES and long_edge <= LONG_EDGE_CAP and short_edge >= SHORT_EDGE_MIN
        print(f"{name:18} {width:>4}x{height:<4} {size:>7} bytes  {colours:>3} colours  {'ok' if within else 'OUT OF CAPS'}")
        ok = ok and within
    if not ok:
        raise SystemExit("at least one screenshot is outside the caps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
