#!/usr/bin/env python3
"""Acceptance sweep for the Leonida Legend trophy tracker.

Drives the real app in Chromium over `node serve.ts` and asserts the behaviour
the entry promises: a progress header that counts and stores, a card per
trophy with its guide and citations, grade/type/text filtering, a spoiler
shield that masks unearned story trophies, an eight-stage roadmap, a missable
register, export/import/reset, keyboard affordances and a layout that fits
both required viewports without a horizontal scrollbar.

Every check prints its measured value, so a pass is evidence rather than an
assertion. Exit status is 0 only when the whole suite passes.

    node serve.ts &
    python3 tools/acceptance.py
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

from playwright.sync_api import Page, sync_playwright

BASE = "http://localhost:8080/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "app" / "data" / "trophies.json"
SCRATCH = pathlib.Path("/root/.makefun/build-home/cache/scratch")
VIEWPORTS = ((1280, 800), (1920, 1080))

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"{mark}  {label}{f' -- {detail}' if detail else ''}")


def section(title: str) -> None:
    print(f"\n--- {title} " + "-" * max(0, 64 - len(title)))


def text_of(page: Page, selector: str) -> str:
    return page.locator(selector).inner_text().replace("\n", " ").strip()


def main() -> int:
    doc = json.loads(DATA.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = doc["trophies"]
    by_id = {t["id"]: t for t in items}
    hidden_ids = {t["id"] for t in items if t["hidden"]}
    missable_ids = {t["id"] for t in items if t["missable"]}

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        errors: list[str] = []
        requests: list[str] = []
        page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))
        page.on(
            "console",
            lambda msg: errors.append(f"console.{msg.type}: {msg.text}") if msg.type == "error" else None,
        )
        page.on("request", lambda req: requests.append(req.url))

        page.goto(BASE, wait_until="load")
        page.wait_for_selector(".card")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="load")
        page.wait_for_selector(".card")

        # ---------------------------------------------------------- header
        section("progress header")
        check(
            text_of(page, "#earned-count") == "0" and text_of(page, "#total-count") == str(len(items)),
            "header starts at 0 / 55",
            text_of(page, "#progress-label"),
        )

        earned_ids = (2, 3, 8)
        for tid in earned_ids:
            page.locator(f'.card[data-id="{tid}"] .check').click()
        page.wait_for_timeout(220)

        earned_now = len(earned_ids)
        check(text_of(page, "#earned-count") == str(earned_now), "count updates on tick", text_of(page, "#progress-label"))
        check(
            text_of(page, "#pct") == f"{round(earned_now / len(items) * 100)}%",
            "percentage follows the count",
            text_of(page, "#pct"),
        )
        fill_w = page.locator("#bar-fill").evaluate("e => e.getBoundingClientRect().width")
        track_w = page.locator("#bar").evaluate("e => e.getBoundingClientRect().width")
        check(
            fill_w > 0 and abs(fill_w / track_w - earned_now / len(items)) < 0.02,
            "bar fill is proportional",
            f"{fill_w:.1f}/{track_w:.1f}px",
        )
        expected_left = len(missable_ids - set(earned_ids))
        shown_left = int(text_of(page, "#missable-left").split()[0])
        check(shown_left == expected_left, "missable counter excludes earned", f"{shown_left} shown, {expected_left} expected")

        # ---------------------------------------------------------- cards
        section("checklist cards")
        card = page.locator('.card[data-id="8"]')
        card_text = card.inner_text()
        check("Trust" in card_text and "Breakfast Run" in card_text, "card carries name and description")
        check(len(card_text.split()) > 50, "card carries the written guide", f"{len(card_text.split())} words")
        link_count = card.locator(".src").count()
        check(link_count >= 1, "citations render as links", f"{link_count} links")
        badge = text_of(page, '.card[data-id="8"] .badge')
        check(bool(badge), "grade badge is shown", badge)
        earned_cards = page.locator(".card.is-earned").count()
        check(earned_cards == earned_now, "earned cards carry their state", f"{earned_cards} cards")

        page.reload(wait_until="load")
        page.wait_for_selector(".card")
        check(text_of(page, "#earned-count") == str(earned_now), "progress survives a reload", text_of(page, "#earned-count"))

        # ---------------------------------------------------------- filters
        section("filters and search")
        silver_total = sum(1 for t in items if t["grade"] == "silver")
        page.locator('#grade-pills .pill[data-grade="silver"]').click()
        page.wait_for_timeout(140)
        check(
            text_of(page, "#result-count") == f"Showing {silver_total} of {len(items)} trophies",
            "grade filter narrows the list",
            text_of(page, "#result-count"),
        )

        page.locator('#grade-pills .pill[data-grade="all"]').click()
        collectible_total = sum(1 for t in items if t["kind"] == "collectibles")
        page.locator('#kind-pills .pill[data-kind="collectibles"]').click()
        page.wait_for_timeout(140)
        check(
            text_of(page, "#result-count") == f"Showing {collectible_total} of {len(items)} trophies",
            "type filter narrows the list",
            text_of(page, "#result-count"),
        )

        page.locator('#kind-pills .pill[data-kind="missable"]').click()
        page.wait_for_timeout(140)
        check(
            text_of(page, "#result-count") == f"Showing {len(missable_ids)} of {len(items)} trophies",
            "missable filter isolates the twelve",
            text_of(page, "#result-count"),
        )

        page.locator('#kind-pills .pill[data-kind="all"]').click()
        page.locator('#grade-pills .pill[data-grade="all"]').click()
        page.fill("#search", "shooting range")
        page.wait_for_timeout(260)
        hits = page.locator(".card").count()
        check(0 < hits < len(items), "search matches on guide text", f"{hits} cards for 'shooting range'")

        page.fill("#search", "zzzzz")
        page.wait_for_timeout(260)
        check(page.locator("#empty").is_visible(), "empty state appears for a dead search")
        page.locator("#clear-filters").click()
        page.wait_for_timeout(220)
        restored = page.locator(".card").count()
        check(restored == len(items), "clear filters restores every card", f"{restored} cards")

        # ---------------------------------------------------------- spoiler
        section("spoiler shield")
        masked = page.locator(".card.is-locked").count()
        hidden_earned = len(hidden_ids & set(earned_ids))
        check(
            masked == len(hidden_ids) - hidden_earned,
            "shield masks unearned story trophies by default",
            f"{masked} masked of {len(hidden_ids)} hidden, {hidden_earned} already earned",
        )

        locked_id = 4
        locked_text = page.locator(f'.card[data-id="{locked_id}"]').inner_text()
        check(
            "Hidden trophy" in locked_text and "tick to reveal" in locked_text,
            "masked card shows the placeholder",
        )
        secret_name = by_id[locked_id]["name"]
        check(
            secret_name not in locked_text and by_id[locked_id]["description"] not in locked_text,
            "masked card leaks neither name nor description",
            f"name {secret_name!r} absent",
        )

        page.locator(f'.card[data-id="{locked_id}"] .check').click()
        page.wait_for_timeout(220)
        revealed_text = page.locator(f'.card[data-id="{locked_id}"]').inner_text()
        check(by_id[locked_id]["description"] in revealed_text, "ticking a hidden trophy reveals it")

        page.locator("#spoiler").click()
        page.wait_for_timeout(220)
        check(page.locator(".card.is-locked").count() == 0, "switching the shield off shows everything")

        page.locator("#spoiler").click()
        page.wait_for_timeout(220)
        remasked = page.locator(".card.is-locked").count()
        check(
            remasked == len(hidden_ids) - hidden_earned - 1,
            "switching it back re-masks the still-unearned",
            f"{remasked} masked",
        )

        # ---------------------------------------------------------- roadmap
        section("roadmap")
        page.locator("#tab-roadmap").click()
        page.wait_for_timeout(280)
        stages = page.locator(".stage").count()
        check(stages == 8, "eight stages render", f"{stages}")
        chips = page.locator(".tchip").count()
        check(chips == len(items), "every trophy is placed in a stage", f"{chips} chips")
        flags = page.locator(".tchip .mini-flag").count()
        check(flags == len(missable_ids), "missables are flagged on the roadmap", f"{flags} flags")
        titles = page.locator(".stage-title").all_inner_texts()
        check(
            len(titles) == 8 and titles[0].startswith("Arrival"),
            "stage copy comes from the data file",
            titles[0][:44] if titles else "no titles",
        )

        page.locator('.tchip[data-id="22"]').click()
        page.wait_for_timeout(420)
        check(page.locator("#panel-checklist").is_visible(), "a chip jumps back to the checklist")

        # ---------------------------------------------------------- missable
        section("missable register")
        page.locator("#tab-missable").click()
        page.wait_for_timeout(280)
        register = page.locator(".missable-card").count()
        check(register == len(missable_ids), "register lists all twelve", f"{register}")
        reasons = page.locator(".missable-why").all_inner_texts()
        shortest = min((len(r) for r in reasons), default=0)
        check(shortest > 30, "each entry explains how the trophy is lost", f"shortest {shortest} chars")

        # ---------------------------------------------------------- progress file
        section("progress file")
        page.locator("#tab-checklist").click()
        page.wait_for_timeout(220)
        SCRATCH.mkdir(parents=True, exist_ok=True)
        export_path = SCRATCH / "accept-export.json"
        with page.expect_download() as download:
            page.locator("#export").click()
        download.value.save_as(str(export_path))
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        expected_ids = len(earned_ids) + 1
        check(
            isinstance(payload.get("earned"), list) and len(payload["earned"]) == expected_ids,
            "export writes the earned set",
            f"{len(payload['earned'])} ids, {export_path.stat().st_size} bytes",
        )

        page.locator("#reset").click()
        page.wait_for_timeout(280)
        check(page.locator("#reset-dialog").is_visible(), "reset asks before it acts")
        page.locator("#reset-confirm").click()
        page.wait_for_timeout(320)
        check(text_of(page, "#earned-count") == "0", "reset clears the progress", text_of(page, "#earned-count"))

        page.locator("#import-file").set_input_files(str(export_path))
        page.wait_for_timeout(420)
        check(
            text_of(page, "#earned-count") == str(expected_ids),
            "import restores it",
            text_of(page, "#earned-count"),
        )

        bad_path = SCRATCH / "accept-bad.json"
        bad_path.write_text("{not json", encoding="utf-8")
        page.locator("#import-file").set_input_files(str(bad_path))
        page.wait_for_timeout(320)
        check(
            text_of(page, "#earned-count") == str(expected_ids),
            "a malformed import leaves progress alone",
            text_of(page, "#toast"),
        )

        # ---------------------------------------------------------- keyboard & semantics
        section("keyboard and semantics")
        page.locator("body").click(position={"x": 1000, "y": 720})
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement.tagName + '.' + document.activeElement.className")
        outline = page.evaluate("getComputedStyle(document.activeElement).outlineWidth")
        check(outline not in ("0px", ""), "tab focus is visible", f"{focused} outline {outline}")

        page.locator("#search").focus()
        page.keyboard.press("Escape")
        page.wait_for_timeout(180)
        check(
            page.locator("#tab-checklist").get_attribute("aria-selected") == "true",
            "the tablist exposes aria-selected",
        )
        check(
            page.locator("#spoiler").get_attribute("role") == "switch"
            and page.locator("#spoiler").get_attribute("aria-checked") in ("true", "false"),
            "the spoiler control is an aria switch",
        )
        unlabelled = page.evaluate(
            "[...document.querySelectorAll('button')].filter(b => !b.textContent.trim()).map(b => b.getAttribute('aria-label'))"
        )
        check(all(unlabelled), "icon-only buttons carry aria-labels", f"{len(unlabelled)} checked")
        check(
            page.locator("main").count() == 1 and page.locator("aside").count() == 1 and page.locator("header").count() >= 1,
            "semantic landmarks are present",
        )

        # ---------------------------------------------------------- offline
        section("offline")
        local = [u for u in requests if u.startswith(BASE)]
        remote = [u for u in requests if not u.startswith(BASE)]
        served = sorted({u.rsplit("/", 1)[-1] or "index.html" for u in local})
        check(not remote and bool(local), "every request is local", f"{len(requests)} requests, {served}")

        # ---------------------------------------------------------- layout
        section("layout")
        for width, height in VIEWPORTS:
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(280)
            metrics = page.evaluate(
                """() => {
                    const sidebar = document.querySelector('.sidebar');
                    return {
                        scrollWidth: document.documentElement.scrollWidth,
                        innerWidth: window.innerWidth,
                        sidebarFits: sidebar.scrollHeight <= sidebar.clientHeight + 1,
                    };
                }"""
            )
            check(
                metrics["scrollWidth"] <= metrics["innerWidth"] and metrics["sidebarFits"],
                f"no horizontal overflow at {width}x{height}",
                f"scrollWidth {metrics['scrollWidth']} / {metrics['innerWidth']}, sidebar fits {metrics['sidebarFits']}",
            )

        check(not errors, "no console or page errors", "; ".join(errors) or "none")
        browser.close()

    failures = [r for r in RESULTS if not r[0]]
    print()
    print(f"{len(RESULTS) - len(failures)}/{len(RESULTS)} checks passed")
    if failures:
        print("FAILURES:")
        for _, label, detail in failures:
            print(f"  - {label}{f' ({detail})' if detail else ''}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
