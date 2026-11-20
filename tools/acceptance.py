"""End-to-end acceptance sweep of the eight required behaviours, in a real browser."""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080/"
SCRATCH = pathlib.Path("/root/.hermes/cache/scratch")
SCRIPTS_ROOT = pathlib.Path(__file__).resolve().parent.parent
results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        requests: list[str] = []
        page.on("request", lambda r: requests.append(r.url))

        page.goto(BASE, wait_until="load")
        page.wait_for_selector(".card")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_selector(".card")

        # 1 progress header
        check(page.locator("#earned-count").inner_text() == "0" and page.locator("#total-count").inner_text() == "55", "header shows N / 55", page.locator("#progress-label").inner_text().replace("\n", " "))
        for tid in (2, 3, 8):
            page.locator(f'.card[data-id="{tid}"] .check').click()
        page.wait_for_timeout(200)
        bar_w = page.locator("#bar-fill").evaluate("e => e.getBoundingClientRect().width")
        track_w = page.locator("#bar").evaluate("e => e.getBoundingClientRect().width")
        check(page.locator("#earned-count").inner_text() == "3", "count updates on tick", page.locator("#progress-label").inner_text().replace("\n", " "))
        check(page.locator("#pct").inner_text() == "5%", "percentage correct", page.locator("#pct").inner_text())
        check(bar_w > 0 and abs(bar_w / track_w - 3 / 55) < 0.02, "bar fill proportional", f"{bar_w:.1f}/{track_w:.1f}px")
        doc = json.loads((SCRIPTS_ROOT / "app/data/trophies.json").read_text(encoding="utf-8"))
        earned_ids = {2, 3, 8}
        expected_left = sum(1 for x in doc["trophies"] if x["missable"] and x["id"] not in earned_ids)
        shown_left = int(page.locator("#missable-left").inner_text().split()[0])
        check(shown_left == expected_left, "missable still-unearned count", f"{shown_left} shown, {expected_left} expected")

        # 2 checklist card contents
        card = page.locator('.card[data-id="8"]')
        txt = card.inner_text()
        check("Trust" in txt and "Breakfast Run" in txt, "card shows name + description")
        check(len(txt.split()) > 50, "card shows the guide text", f"{len(txt.split())} words in card")
        check(card.locator(".src").count() >= 1, "source links rendered", f"{card.locator('.src').count()} links")
        check(card.locator(".badge").inner_text().strip() != "", "grade badge shown", card.locator(".badge").inner_text().replace("\n", " "))
        check(page.locator(".card.is-earned").count() == 3, "earned state applied", f"{page.locator('.card.is-earned').count()} cards")

        # persistence
        page.reload(wait_until="load")
        page.wait_for_selector(".card")
        check(page.locator("#earned-count").inner_text() == "3", "progress persists across reload", f"key present: {page.evaluate('localStorage.length > 0')}")

        # 3 filters
        page.locator('#grade-pills .pill[data-grade="silver"]').click()
        page.wait_for_timeout(120)
        check(page.locator("#result-count").inner_text() == "Showing 6 of 55 trophies", "grade filter", page.locator("#result-count").inner_text())
        page.locator('#grade-pills .pill[data-grade="all"]').click()
        page.locator('#kind-pills .pill[data-kind="collectibles"]').click()
        page.wait_for_timeout(120)
        check(page.locator("#result-count").inner_text() == "Showing 5 of 55 trophies", "kind filter", page.locator("#result-count").inner_text())
        page.locator('#kind-pills .pill[data-kind="missable"]').click()
        page.wait_for_timeout(120)
        check(page.locator("#result-count").inner_text() == "Showing 12 of 55 trophies", "missable filter", page.locator("#result-count").inner_text())
        page.locator('#kind-pills .pill[data-kind="all"]').click()
        page.locator('#grade-pills .pill[data-grade="all"]').click()
        page.fill("#search", "shooting range")
        page.wait_for_timeout(250)
        n = page.locator(".card").count()
        check(0 < n < 55, "live search filters", f"{n} cards for 'shooting range'")
        page.fill("#search", "zzzzz")
        page.wait_for_timeout(250)
        check(page.locator("#empty").is_visible(), "empty state when nothing matches")
        page.locator("#clear-filters").click()
        page.wait_for_timeout(200)
        check(page.locator(".card").count() == 55, "clear filters restores all", f"{page.locator('.card').count()}")

        # 4 spoiler mode
        hidden_total = sum(1 for x in doc["trophies"] if x["hidden"])
        hidden_earned = sum(1 for x in doc["trophies"] if x["hidden"] and x["id"] in earned_ids)
        masked = page.locator(".card.is-locked").count()
        check(masked == hidden_total - hidden_earned, "spoiler on by default: hidden trophies masked", f"{masked} masked of {hidden_total} hidden, {hidden_earned} already earned")
        locked_text = page.locator('.card[data-id="4"]').inner_text()
        check("Hidden trophy" in locked_text and "tick to reveal" in locked_text, "masked card shows the placeholder")
        check("T**s" not in locked_text and "Chapter 2" not in locked_text, "masked card leaks no name/description")
        page.locator('.card[data-id="4"] .check').click()
        page.wait_for_timeout(200)
        revealed = page.locator('.card[data-id="4"]').inner_text()
        check("Chapter 2" in revealed, "earning a hidden trophy reveals it")
        page.locator("#spoiler").click()
        page.wait_for_timeout(200)
        check(page.locator(".card.is-locked").count() == 0, "spoiler toggle off shows everything")
        page.locator("#spoiler").click()
        page.wait_for_timeout(200)
        remasked = page.locator(".card.is-locked").count()
        check(remasked == hidden_total - hidden_earned - 1, "spoiler toggle back on re-masks unearned", f"{remasked} masked ({hidden_total} hidden, {hidden_earned + 1} earned)")

        # 5 roadmap view
        page.locator("#tab-roadmap").click()
        page.wait_for_timeout(250)
        check(page.locator(".stage").count() == 8, "roadmap renders 8 stages", f"{page.locator('.stage').count()}")
        check(page.locator(".tchip").count() == 55, "roadmap lists every trophy", f"{page.locator('.tchip').count()} chips")
        check(page.locator(".tchip .mini-flag").count() == 12, "roadmap flags missables", f"{page.locator('.tchip .mini-flag').count()} flags")
        stage_titles = page.locator(".stage-title").all_inner_texts()
        check(stage_titles[0].startswith("Arrival") and len(stage_titles) == 8, "stage copy from data", stage_titles[0][:40])
        page.locator('.tchip[data-id="22"]').click()
        page.wait_for_timeout(400)
        check(page.locator("#panel-checklist").is_visible(), "chip jumps to the checklist")

        # 6 missable view
        page.locator("#tab-missable").click()
        page.wait_for_timeout(250)
        check(page.locator(".missable-card").count() == 12, "missable view lists 12", f"{page.locator('.missable-card').count()}")
        whys = page.locator(".missable-why").all_inner_texts()
        check(all(len(w) > 30 for w in whys), "each missable explains how it is lost", f"shortest {min(len(w) for w in whys)} chars")

        # 7 export / import / reset
        page.locator("#tab-checklist").click()
        page.wait_for_timeout(200)
        with page.expect_download() as dl:
            page.locator("#export").click()
        export_path = SCRATCH / "accept-export.json"
        dl.value.save_as(str(export_path))
        payload = json.loads(export_path.read_text())
        check(isinstance(payload["earned"], list) and len(payload["earned"]) == 4, "export writes the earned set", f"{len(payload['earned'])} ids, {export_path.stat().st_size} bytes")

        page.locator("#reset").click()
        page.wait_for_timeout(250)
        check(page.locator("#reset-dialog").is_visible(), "reset asks for confirmation first")
        page.locator("#reset-confirm").click()
        page.wait_for_timeout(300)
        check(page.locator("#earned-count").inner_text() == "0", "reset clears progress", page.locator("#earned-count").inner_text())

        page.locator("#import-file").set_input_files(str(export_path))
        page.wait_for_timeout(400)
        check(page.locator("#earned-count").inner_text() == "4", "import restores progress", page.locator("#earned-count").inner_text())

        bad = SCRATCH / "accept-bad.json"
        bad.write_text("{not json")
        page.locator("#import-file").set_input_files(str(bad))
        page.wait_for_timeout(300)
        check(page.locator("#earned-count").inner_text() == "4", "invalid import leaves progress intact", page.locator("#toast").inner_text())

        # 8 accessibility
        page.locator("body").click(position={"x": 1000, "y": 720})
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement.tagName + '.' + document.activeElement.className")
        outline = page.evaluate("getComputedStyle(document.activeElement).outlineWidth")
        check(outline not in ("0px", ""), "visible focus ring on tab", f"{focused} outline {outline}")
        page.locator("#search").focus()
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        check(page.locator("#tab-checklist").get_attribute("aria-selected") == "true", "tablist exposes aria-selected")
        check(page.locator("#spoiler").get_attribute("role") == "switch" and page.locator("#spoiler").get_attribute("aria-checked") in ("true", "false"), "spoiler is an aria switch")
        labels = page.evaluate("[...document.querySelectorAll('button')].filter(b => !b.textContent.trim()).map(b => b.getAttribute('aria-label'))")
        check(all(labels), "icon-only buttons have aria-labels", f"{len(labels)} checked")
        check(page.locator("main").count() == 1 and page.locator("aside").count() == 1 and page.locator("header").count() >= 1, "semantic landmarks present")

        # no network beyond the four local files
        local_only = all(u.startswith(BASE) for u in requests)
        check(local_only and len([u for u in requests if u.startswith(BASE)]) > 0, "every request is local", f"{len(requests)} requests, {sorted({u.rsplit('/',1)[-1] for u in requests})}")

        # layout at both required sizes
        for w, h in ((1280, 800), (1920, 1080)):
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(250)
            m = page.evaluate("({sw: document.documentElement.scrollWidth, iw: innerWidth, sb: document.querySelector('.sidebar').scrollHeight <= document.querySelector('.sidebar').clientHeight + 1, cards: document.querySelectorAll('.card').length})")
            check(m["sw"] <= m["iw"] and m["sb"], f"no horizontal overflow at {w}x{h}", f"scrollWidth {m['sw']} / {m['iw']}, sidebar fits: {m['sb']}")

        check(not errors, "no console or page errors", "; ".join(errors) or "none")
        browser.close()

    failures = [r for r in results if not r[0]]
    print()
    print(f"{len(results) - len(failures)}/{len(results)} checks passed")
    if failures:
        print("FAILURES:", [f[1] for f in failures])
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
