"""Capture the four submission screenshots at 1280x800 and keep each well under 256 KiB."""
import io
import pathlib
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = ROOT / "screenshots"
BASE = "http://localhost:8080/"
VIEWPORT = {"width": 1280, "height": 800}
EARNED = [2, 3, 4, 5, 8, 9, 10, 21, 44, 46, 51, 22, 23, 24]
MAX_BYTES = 256 * 1024
SAFE_BYTES = 200 * 1024


def shrink(path: pathlib.Path) -> tuple[int, int]:
    """Re-encode as a 256-colour PNG when the capture is close to the cap."""
    raw = path.read_bytes()
    if len(raw) <= SAFE_BYTES:
        return len(raw), 100
    src = Image.open(io.BytesIO(raw)).convert("RGB")
    best = None
    for colours in (256, 192, 128):
        quant = src.quantize(colors=colours, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        buf = io.BytesIO()
        quant.save(buf, "PNG", optimize=True)
        data = buf.getvalue()
        if len(data) <= SAFE_BYTES:
            best = (data, colours)
            break
    if best is None:
        raise SystemExit(f"{path.name} cannot be compressed under {SAFE_BYTES} bytes")
    path.write_bytes(best[0])
    return len(best[0]), best[1]


def main() -> int:
    SHOTS.mkdir(exist_ok=True)
    for old in list(SHOTS.glob("*.jpg")) + list(SHOTS.glob("*.jpeg")):
        old.unlink()
        print("removed", old.name)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)
        page.goto(BASE, wait_until="load")
        page.wait_for_selector(".card")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_selector(".card")
        for tid in EARNED:
            page.locator(f'.card[data-id="{tid}"] .check').click()
        page.wait_for_timeout(400)
        # the toast sits over the third card; hide it and freeze it hidden before any capture
        page.evaluate("document.getElementById('toast').classList.remove('is-visible')")
        page.add_style_tag(content="#toast{display:none !important}")
        print("progress:", page.locator("#earned-count").inner_text(), page.locator("#pct").inner_text())

        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        # cover: clip so the frame ends in the gap below the second card, never mid-card
        box = page.locator('.card[data-id="4"]').bounding_box() or {"y": 620, "height": 200}
        # end the frame exactly in the gap under the last fully visible card, never mid-card
        bottoms = []
        for i in range(page.locator(".card").count()):
            b = page.locator(".card").nth(i).bounding_box()
            if b:
                bottoms.append(int(b["y"] + b["height"] + 16))
        cut = max([b for b in bottoms if b <= 1010] or [int(box["y"] + box["height"] + 16)])
        cut = max(480, min(cut, 1280))
        print("cover height:", cut)
        page.set_viewport_size({"width": 1280, "height": cut})
        page.wait_for_timeout(400)
        page.screenshot(path=str(SHOTS / "1-cover.png"))
        page.set_viewport_size(VIEWPORT)

        page.evaluate('document.querySelector(\'.card[data-id="8"]\').scrollIntoView({block:"start"})')
        page.wait_for_timeout(300)
        page.evaluate("window.scrollBy(0, -130)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "2-checklist.png"))

        page.locator("#tab-roadmap").click()
        page.wait_for_timeout(350)
        page.evaluate("window.scrollTo(0, 0)")
        # fit all 8 roadmap stages into one frame: shrink the page, then capture the viewport
        page.add_style_tag(content="body{zoom:0.66}")
        page.wait_for_timeout(500)
        page.screenshot(path=str(SHOTS / "3-roadmap.png"))

        page.locator("#tab-missable").click()
        page.wait_for_timeout(350)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "4-missable.png"))
        browser.close()

    for name in ("1-cover.png", "2-checklist.png", "3-roadmap.png", "4-missable.png"):
        path = SHOTS / name
        size, colours = shrink(path)
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            print(f"{name}: {im.size[0]}x{im.size[1]} {im.format} {size} bytes ({colours} colours)")
        if size > MAX_BYTES:
            raise SystemExit(f"{name} exceeds {MAX_BYTES} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
