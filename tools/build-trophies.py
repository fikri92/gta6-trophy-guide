#!/usr/bin/env python3
"""Assemble app/data/trophies.json for the Leonida Legend tracker.

Two inputs meet in this file, and the script keeps them apart on purpose:

  * the official PlayStation 5 list -- trophy id, grade, name and description.
    Those strings are quoted here verbatim and never edited by the build.
  * the authored layer -- a written guide for every trophy, the per-trophy
    citations, the roadmap stages, flags and notes. That copy lives in
    app/data/trophies.json and is checked, not regenerated: rewriting it from
    a template would flatten the voice the guide is written in.

So `python3 tools/build-trophies.py` is a validator that rewrites the file in
canonical form: it re-derives every field it owns (names, grades, ids, order,
kind, stage, flags, citations, roadmap, meta) and fails loudly if the authored
guides drift out of shape or an official string no longer matches the list.

    python3 tools/build-trophies.py           # validate and rewrite in place
    python3 tools/build-trophies.py --check    # validate only, write nothing
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "app" / "data" / "trophies.json"

GAME = "Grand Theft Auto VI"
PLATFORM = "PlayStation 5"
LIST_LABEL = "the official 55 trophies, 2026-11-18"

GUIDE_MIN_WORDS = 40
GUIDE_MAX_WORDS = 110
VALID_KINDS = ("story", "collectibles", "activities", "online", "platinum")

# --------------------------------------------------------------------------
# The official list. Id, grade, name and description, quoted exactly as
# PlayStation publishes them. Do not reword anything in this block.
# --------------------------------------------------------------------------

OFFICIAL: tuple[tuple[int, str, str, str], ...] = (
    (1, "platinum", "Vice Got a Price!",
     "Congratulations! You're a Leonida Legend."),
    (2, "bronze", "Just Like Paradise",
     "Complete Gone Fishing."),
    (3, "bronze", "Paradise Lost",
     "Complete Chapter 1."),
    (4, "bronze", "T**s Ass Drug Money",
     "Complete Chapter 2."),
    (5, "bronze", "Vice City, Baby!",
     "Complete Chapter 3."),
    (6, "bronze", "Top Of The World, Ma",
     "Complete Chapter 4."),
    (7, "gold", "You Gotta Know When to Get Off",
     "Complete the final mission."),
    (8, "bronze", "Trust",
     "Complete Breakfast Run."),
    (9, "bronze", "Break the Bank",
     "Complete The Cartel Heist."),
    (10, "bronze", "Family Matters",
     "Complete Child's Play."),
    (11, "bronze", "DWNFALL",
     "Complete Headliners."),
    (12, "bronze", "Hi-Jacked",
     "Complete VCIA Takedown."),
    (13, "bronze", "Snow Storm",
     "Complete Operation Savage Glory."),
    (14, "gold", "A Long Road",
     "Attain 100% Completion."),
    (15, "silver", "Cunning Stunts",
     "Complete 250 Stunts."),
    (16, "bronze", "Master of None",
     "Try each type of activity once."),
    (17, "silver", "The Shootist",
     "Earn a gold medal in all Shooting Range challenges."),
    (18, "bronze", "Top Fun",
     "Win a Top Fun Drone Race at every location."),
    (19, "bronze", "Earn Cash, Not Kudos",
     "Win 20 different races."),
    (20, "bronze", "Baited My Tackle",
     "Beat Cal in a fishing challenge."),
    (21, "bronze", "Stick Fiddler",
     "Complete an arcade game."),
    (22, "bronze", "Road to Rehabilitation",
     "Complete the final mission for Andy."),
    (23, "bronze", "This Was No Boat Accident",
     "Complete the final mission for Kenton."),
    (24, "bronze", "The Lone Rider",
     "Complete the final mission for Billy."),
    (25, "silver", "Strangers & Freaks",
     "Complete 8 mission strands for strangers across the state of Leonida."),
    (26, "bronze", "Supply & Demand",
     "Complete the final mission for Randy."),
    (27, "bronze", "Spin On This!",
     "Complete the final mission for Tyrone."),
    (28, "bronze", "Positive Mental Attitude",
     "Meditate at every spot across Leonida."),
    (29, "bronze", "Fair Game",
     "Hunt a unique animal for Bret."),
    (30, "silver", "Don't Touch My Deck",
     "Complete 3 Collectible Card sets."),
    (31, "silver", "You WAiNKer!",
     "WAiNK It at 100 locations."),
    (32, "bronze", "One Last Thing",
     "Complete 50 Challenges."),
    (33, "bronze", "Hot Together",
     "Lose a 4 star Wanted Level with your partner and escape the heat."),
    (34, "bronze", "Retail Therapy",
     "Rob 3 shops back-to-back with your partner without losing your Wanted Level."),
    (35, "bronze", "Whip It Good",
     "Discover 100 vehicles."),
    (36, "bronze", "Gunslinger",
     "Take down 5 enemies in a single use of Combat Focus."),
    (37, "bronze", "Catch Me If You Can",
     "Make an unscheduled departure at VCIA."),
    (38, "bronze", "Challenging Tank",
     "Kinda hot in these Rhinos."),
    (39, "bronze", "Sneakthief",
     "Rob a jewelry store without being detected."),
    (40, "silver", "Maximum Withdrawal",
     "Rob 5 Bank Vaults and escape."),
    (41, "bronze", "A Classic Blitz Play",
     "Rob an Armored Truck and escape."),
    (42, "bronze", "The Goodtime State",
     "Explore all of Leonida."),
    (43, "bronze", "Pest Control",
     "Rob an Illegal Operation belonging to each gang."),
    (44, "bronze", "In The Beginning…",
     "Enjoy a cocktail with a view on Ocean Beach."),
    (45, "bronze", "Capital Offense",
     "Smash your way out of a vehicle showroom in classic style."),
    (46, "bronze", "Let’s Go Bowling",
     "Follow-through at the Kolt & Associates' bowling alley."),
    (47, "bronze", "Personal Best",
     "A partnership with mass appeal."),
    (48, "bronze", "Actions Speak Louder",
     "Choices made (for better or worse)."),
    (49, "bronze", "Bad Luck, I Guess",
     "Second time's the charm."),
    (50, "bronze", "The Truth Is Out There",
     "What the hell just happened?"),
    (51, "bronze", "Ten Pin",
     "Bowl 'em over with a melee drive-by."),
    (52, "bronze", "Dime on the Dollar",
     "Earn $250,000 laundering Marked Bills through your contacts."),
    (53, "bronze", "Treat Yo Self",
     "Spend $100,000 across all shops."),
    (54, "bronze", "Little Boxes",
     "Purchase all garage properties."),
    (55, "bronze", "On the Spot",
     "Register 10 vehicles to the Scooter Bros app."),
)

# --------------------------------------------------------------------------
# Citations. Mentioned by key in PLACEMENT below, expanded to full objects.
# --------------------------------------------------------------------------

SOURCES: dict[str, dict[str, str]] = {
    "psn": {"name": "PSNProfiles trophy guide",
            "url": "https://psnprofiles.com/guide/19042-grand-theft-auto-vi-trophy-guide"},
    "ppyx": {"name": "PowerPyx trophy guide & roadmap",
             "url": "https://www.powerpyx.com/grand-theft-auto-vi-trophy-guide-roadmap/"},
    "exo": {"name": "Exophase trophy list",
            "url": "https://www.exophase.com/game/grand-theft-auto-vi-ps5/trophies/"},
    "ign": {"name": "IGN wiki: trophies",
            "url": "https://www.ign.com/wikis/grand-theft-auto-6/Trophies"},
    "wiki": {"name": "GTA Wiki: trophies in GTA VI",
             "url": "https://gta.fandom.com/wiki/Trophies_in_GTA_VI"},
    "wiki_act": {"name": "GTA Wiki: activities in Leonida",
                 "url": "https://gta.fandom.com/wiki/Activities_in_GTA_VI"},
    "ppyx_col": {"name": "PowerPyx collectibles guide",
                 "url": "https://www.powerpyx.com/grand-theft-auto-vi-all-collectibles-guide/"},
    "ign_map": {"name": "IGN wiki: Leonida map & districts",
                "url": "https://www.ign.com/wikis/grand-theft-auto-6/Leonida"},
}

# --------------------------------------------------------------------------
# Placement: (stage, kind, missable, hidden, citations) per trophy id.
# Stage is the roadmap slot the trophy is worked in, not the chapter it
# unlocks in -- the two differ for cleanup trophies, which is the point.
# `hidden` marks story material the spoiler shield masks.
# --------------------------------------------------------------------------

PLACEMENT: dict[int, tuple[int, str, bool, bool, tuple[str, ...]]] = {
    1: (8, "platinum", False, False, ("psn", "ppyx", "exo")),
    2: (1, "story", False, True, ("psn", "ppyx", "ign")),
    3: (2, "story", False, True, ("psn", "ign", "wiki")),
    4: (3, "story", False, True, ("psn", "ign")),
    5: (3, "story", False, True, ("psn", "ppyx")),
    6: (4, "story", False, True, ("psn", "ign")),
    7: (4, "story", False, True, ("ppyx", "psn", "wiki")),
    8: (2, "story", False, True, ("psn", "ign")),
    9: (3, "story", False, True, ("psn", "ppyx")),
    10: (3, "story", False, True, ("psn", "ign")),
    11: (3, "story", False, True, ("psn", "wiki")),
    12: (3, "story", False, True, ("psn", "ign")),
    13: (4, "story", False, True, ("ppyx", "psn")),
    14: (7, "activities", False, False, ("ppyx", "psn", "ign")),
    15: (7, "activities", False, False, ("ppyx", "wiki_act")),
    16: (7, "activities", False, False, ("wiki_act", "psn")),
    17: (7, "activities", False, False, ("ppyx", "wiki_act")),
    18: (7, "activities", False, False, ("wiki_act", "ppyx")),
    19: (7, "activities", False, False, ("wiki_act", "psn")),
    20: (5, "activities", True, False, ("psn", "wiki_act")),
    21: (1, "activities", False, False, ("wiki_act", "psn")),
    22: (5, "activities", True, False, ("psn", "wiki")),
    23: (5, "activities", True, False, ("psn", "wiki")),
    24: (5, "activities", True, False, ("psn", "wiki")),
    25: (5, "activities", True, False, ("psn", "ign", "wiki")),
    26: (5, "activities", True, False, ("psn", "wiki")),
    27: (5, "activities", True, False, ("psn", "wiki")),
    28: (7, "collectibles", False, False, ("ppyx_col", "ign_map")),
    29: (5, "activities", True, False, ("psn", "wiki_act")),
    30: (7, "collectibles", False, False, ("ppyx_col", "psn")),
    31: (7, "collectibles", False, False, ("ppyx_col", "wiki_act")),
    32: (7, "activities", False, False, ("wiki_act", "psn")),
    33: (3, "activities", True, False, ("psn", "ppyx")),
    34: (3, "activities", True, False, ("psn", "ppyx")),
    35: (7, "collectibles", False, False, ("ppyx", "wiki")),
    36: (7, "activities", False, False, ("psn", "wiki_act")),
    37: (6, "activities", False, False, ("psn", "wiki")),
    38: (6, "activities", False, False, ("psn", "wiki")),
    39: (6, "activities", False, False, ("psn", "ppyx")),
    40: (6, "activities", False, False, ("psn", "ppyx", "wiki")),
    41: (6, "activities", False, False, ("psn", "wiki")),
    42: (7, "collectibles", False, False, ("ign_map", "ppyx_col")),
    43: (6, "activities", False, False, ("psn", "wiki_act")),
    44: (1, "activities", False, False, ("psn", "wiki")),
    45: (6, "activities", False, False, ("psn", "wiki")),
    46: (1, "activities", False, False, ("psn", "wiki_act")),
    47: (5, "activities", True, False, ("psn", "ign")),
    48: (2, "activities", False, False, ("psn", "ign")),
    49: (2, "activities", False, False, ("psn", "wiki")),
    50: (5, "activities", True, False, ("psn", "wiki")),
    51: (1, "activities", False, False, ("psn", "wiki_act")),
    52: (6, "activities", False, False, ("psn", "ppyx")),
    53: (6, "activities", False, False, ("psn", "wiki")),
    54: (6, "activities", False, False, ("psn", "ppyx")),
    55: (6, "activities", False, False, ("psn", "wiki_act")),
}

# How a missable is lost, in one sentence. Only missable trophies carry these.
MISSABLE_NOTES: dict[int, str] = {
    20: "Cal's contest is only offered during a short window in Kenton's strand; once the strand closes the pier is empty.",
    22: "Andy's strand disappears when Chapter 4 ends: the airport drop-off is his final mission.",
    23: "Kenton's salvage chain closes with the cartel thread at the end of Chapter 3.",
    24: "Billy shuts the shop for good when Chapter 4 begins.",
    25: "Three of the eight strands expire as the story advances; leave them too long and the silver is gone.",
    26: "Randy's gun-running chain is removed after the final heist unlocks.",
    27: "Tyrone's drift strand vanishes when the endgame marker appears.",
    29: "The panther only spawns during Bret's mission; abandoning it ends the strand permanently.",
    33: "Needs your partner following you, which ends once the story splits the crew.",
    34: "The partner ride-along ends after Chapter 3, and all three robberies must happen in one run.",
    47: "A one-off interview prompt in Chapter 3; the scene never repeats.",
    50: "The swamp encounter is chapter-gated and cannot be replayed after the finale.",
}

ROADMAP: tuple[tuple[int, str, str], ...] = (
    (1, "Arrival: the first night in Vice City",
     "Gone Fishing, the boardwalk arcade, the Ocean Beach bar, the bowling alley and a melee drive-by are all "
     "reachable before the first story marker. Clear them in one pass so the early map is already paying out."),
    (2, "Chapter 1: Port Gellhorn and the first score",
     "Push the chapter, run the two optional prep jobs, and use the quiet stretches to bank the choice and retry "
     "trophies. Nothing here can be missed yet, so this is the stage to experiment."),
    (3, "Chapters 2 and 3: cartel money and headlines",
     "Hot Together and Retail Therapy both need your partner riding with you, so finish them early in the chapter, "
     "before the crew splits."),
    (4, "Chapter 4 and the road to the finale",
     "Save manually before the boardroom marker. Finish every side strand you have opened before the finale unlocks, "
     "because this is the last safe point."),
    (5, "Side strands before the point of no return",
     "Ten of the twelve missables sit here: Andy, Kenton, Billy, Randy and Tyrone, the Strangers strand count, "
     "Cal's fishing contest, Bret's hunt, the interview and the swamp encounter."),
    (6, "Heists, robberies and the money game",
     "Free-roam robberies, the five bank vaults, the armoured truck, the gang operations and the property purchases. "
     "Bring a thermal drill, a suppressed weapon and a fast car."),
    (7, "Collectibles, exploration and 100% cleanup",
     "Meditation spots, card sets, WAiNK posts, vehicles, districts, challenges and 250 stunts. Finish activities "
     "before you sweep pickups, because some collectibles only spawn once their activity is done."),
    (8, "The platinum",
     "Vice Got a Price! registers automatically once the other fifty-four trophies are on your profile. There is no "
     "extra step and no way to rush it."),
)

SOURCE_NOTE = (
    "Trophy names and descriptions follow the official PlayStation 5 list for Grand Theft Auto VI (55 trophies, "
    "captured 18 November 2026). Guides, roadmap, missable warnings and stage order are original write-ups for this "
    "tracker. The PSNProfiles, Exophase, PowerPyx, IGN and GTA Wiki pages are reference reading only: the app renders "
    "them as plain links and never fetches them."
)

# Field order in the written file, so diffs stay readable across rebuilds.
FIELD_ORDER = ("id", "name", "description", "grade", "guide", "sources",
               "kind", "missable", "stage", "hidden", "missable_note")


class BuildError(Exception):
    """Raised when the authored data and the official list disagree."""


def load_authored() -> dict[int, str]:
    """Read the guide strings already written into the data file."""
    try:
        current = json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuildError(f"cannot read {DATA.relative_to(ROOT)}: {exc}") from exc
    guides: dict[int, str] = {}
    for item in current.get("trophies", []):
        guide = item.get("guide")
        if isinstance(guide, str) and guide.strip():
            guides[item["id"]] = guide.strip()
    return guides


def check_official(authored: dict[int, str], existing: dict[int, dict]) -> None:
    """The official strings on disk must still match OFFICIAL, byte for byte."""
    drift: list[str] = []
    for tid, grade, name, description in OFFICIAL:
        seen = existing.get(tid)
        if seen is None:
            drift.append(f"{tid}: missing from the data file")
            continue
        for field, want in (("name", name), ("description", description), ("grade", grade)):
            if seen.get(field) != want:
                drift.append(f"{tid}: {field} {seen.get(field)!r} != {want!r}")
    if drift:
        raise BuildError("official text drifted from the list:\n  " + "\n  ".join(drift))
    missing = [tid for tid, *_ in OFFICIAL if tid not in authored]
    if missing:
        raise BuildError(f"trophies with no written guide: {missing}")
    extra = sorted(set(authored) - {tid for tid, *_ in OFFICIAL})
    if extra:
        raise BuildError(f"guides for ids not in the official list: {extra}")


def check_guides(authored: dict[int, str]) -> None:
    """Word bounds, so no card ships a stub or an essay."""
    bad = []
    for tid, _, name, _ in OFFICIAL:
        words = len(authored[tid].split())
        if not GUIDE_MIN_WORDS <= words <= GUIDE_MAX_WORDS:
            bad.append(f"{tid} {name!r}: {words} words")
    if bad:
        raise BuildError(
            f"guides must be {GUIDE_MIN_WORDS}-{GUIDE_MAX_WORDS} words:\n  " + "\n  ".join(bad)
        )


def check_placement() -> None:
    """Every official id placed once, every citation key real."""
    ids = {tid for tid, *_ in OFFICIAL}
    if set(PLACEMENT) != ids:
        raise BuildError(f"PLACEMENT ids differ from the list: {sorted(set(PLACEMENT) ^ ids)}")
    for tid, (stage, kind, missable, _hidden, cites) in PLACEMENT.items():
        if not 1 <= stage <= 8:
            raise BuildError(f"{tid}: stage {stage} outside 1-8")
        if kind not in VALID_KINDS:
            raise BuildError(f"{tid}: kind {kind!r} not in {VALID_KINDS}")
        if not 1 <= len(cites) <= 3:
            raise BuildError(f"{tid}: {len(cites)} citations, want 1-3")
        unknown = [c for c in cites if c not in SOURCES]
        if unknown:
            raise BuildError(f"{tid}: unknown citation keys {unknown}")
    notes = {tid for tid, (_, _, missable, _, _) in PLACEMENT.items() if missable}
    if notes != set(MISSABLE_NOTES):
        raise BuildError(f"MISSABLE_NOTES ids differ from missable flags: {sorted(notes ^ set(MISSABLE_NOTES))}")
    if [s for s, _, _ in ROADMAP] != list(range(1, 9)):
        raise BuildError("ROADMAP must be exactly stages 1-8 in order")


def build(authored: dict[int, str]) -> dict:
    trophies = []
    for tid, grade, name, description in OFFICIAL:
        stage, kind, missable, hidden, cites = PLACEMENT[tid]
        item = {
            "id": tid,
            "name": name,
            "description": description,
            "grade": grade,
            "guide": authored[tid],
            "sources": [SOURCES[c] for c in cites],
            "kind": kind,
            "missable": missable,
            "stage": stage,
            "hidden": hidden,
        }
        if missable:
            item["missable_note"] = MISSABLE_NOTES[tid]
        trophies.append({field: item[field] for field in FIELD_ORDER if field in item})

    return {
        "game": GAME,
        "platform": PLATFORM,
        "list": LIST_LABEL,
        "trophies": trophies,
        "roadmap": [{"stage": s, "title": t, "detail": d} for s, t, d in ROADMAP],
        "meta": {
            "missable_count": sum(1 for *_, missable, _h, _c in PLACEMENT.values() if missable),
            "source_note": SOURCE_NOTE,
        },
    }


def summarise(doc: dict) -> None:
    by_grade: dict[str, int] = {}
    by_stage: dict[int, int] = {}
    words: list[int] = []
    for t in doc["trophies"]:
        by_grade[t["grade"]] = by_grade.get(t["grade"], 0) + 1
        by_stage[t["stage"]] = by_stage.get(t["stage"], 0) + 1
        words.append(len(t["guide"].split()))
    grades = " ".join(f"{g} {by_grade.get(g, 0)}" for g in ("platinum", "gold", "silver", "bronze"))
    stages = " ".join(f"s{s}:{by_stage[s]}" for s in range(1, 9))
    print(f"  trophies   {len(doc['trophies'])}  ({grades})")
    print(f"  stages     {stages}")
    print(f"  guides     {min(words)}-{max(words)} words, {sum(words)} total")
    print(f"  sources    {sum(len(t['sources']) for t in doc['trophies'])} citations")
    print(f"  missable   {doc['meta']['missable_count']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble and validate app/data/trophies.json.")
    parser.add_argument("--check", action="store_true", help="validate only, do not write")
    args = parser.parse_args()

    print(f"building {DATA.relative_to(ROOT)}")
    try:
        authored = load_authored()
        try:
            existing = {t["id"]: t for t in json.loads(DATA.read_text(encoding="utf-8"))["trophies"]}
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            raise BuildError(f"cannot read the existing trophy list: {exc}") from exc
        check_official(authored, existing)
        check_placement()
        check_guides(authored)
        doc = build(authored)
    except BuildError as exc:
        print(f"FAILED  {exc}", file=sys.stderr)
        return 1

    summarise(doc)
    if args.check:
        print("OK  valid; nothing written (--check)")
        return 0

    DATA.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK  wrote {DATA.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
