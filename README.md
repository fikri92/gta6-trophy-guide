# Leonida Legend — a GTA VI trophy guide and tracker

[![make.fun · gta6-trophy-guide-01](https://make.fun/badge/gta6-trophy-guide-01.svg)](https://make.fun/bounty/gta6-trophy-guide-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-guide-01)
[![rank](https://make.fun/badge/gta6-trophy-guide-01/fikri92/gta6-trophy-guide/rank.svg)](https://make.fun/bounty/gta6-trophy-guide-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-guide-01)
[![reward](https://make.fun/badge/gta6-trophy-guide-01/fikri92/gta6-trophy-guide/reward.svg)](https://make.fun/bounty/gta6-trophy-guide-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-guide-01)

An offline guide and tracker for the 55 PlayStation 5 trophies of Grand Theft Auto VI.
Three views over the same list: a checklist carrying a written guide and its sources for
every trophy, a roadmap of eight stages that keeps the missables reachable, and a register
of the twelve trophies that can be lost for good. Progress lives in the browser, exports to
a file and imports back.

Static files, no build step, no frameworks, no network at run time.

## Run it

```sh
node serve.ts            # http://localhost:8080
```

`--port 9000` picks another port. Opening `app/index.html` straight off the disk will not
work: the app reads `data/trophies.json` with `fetch`, and `file://` forbids that.

## What is in the box

| Path | What it is |
| --- | --- |
| `app/index.html` | the page: header, controls, three panels, one inline SVG sprite |
| `app/style.css` | the whole look — Vice City palette, teal working accent, magenta for missable and platinum |
| `app/app.js` | the tracker: rendering, filters, spoiler shield, `localStorage`, export/import |
| `app/data/trophies.json` | 55 trophies with guides, citations, stages, flags, the roadmap and the meta note |
| `screenshots/` | the four submission images |
| `tools/` | the build, acceptance, screenshot and verification scripts |
| `main.ts`, `serve.ts` | the submission harness and a local static server |
| `vendor/` | the make.fun dossier builder — leave it alone |

## The data file

`app/data/trophies.json` is the whole content of the guide. Each trophy carries:

```json
{
  "id": 8,
  "name": "Trust",
  "description": "Complete Breakfast Run.",
  "grade": "bronze",
  "guide": "Breakfast Run is the early-morning diner job in Port Gellhorn. …",
  "sources": [{ "name": "PSNProfiles trophy guide", "url": "https://…" }],
  "kind": "story",
  "missable": false,
  "stage": 2,
  "hidden": true
}
```

`stage` is where a trophy is *worked*, which is not always the chapter it unlocks in —
cleanup trophies sit in stage 6 and 7 even when they become available in stage 2. `hidden`
marks story material the spoiler shield masks. `missable` trophies also carry a
`missable_note` naming the moment they become unreachable.

Source URLs are citations and are only ever rendered as plain links. The app never fetches
one, and there is no webfont, no external stylesheet, no CDN and no analytics.

## Tools

```sh
node serve.ts &                              # everything below needs the server
python3 tools/acceptance.py                  # 44 behaviour checks in Chromium
python3 tools/screenshots.py                 # recapture screenshots/
python3 tools/verify.py                      # static pre-submission gate
python3 tools/build-trophies.py --check      # data schema, word bounds, official text
```

`tools/build-trophies.py` holds the official list — id, grade, name, description — and
re-derives everything else around the written guides. It refuses to build if a name or
description drifts from the list, if a guide falls outside 40–110 words, or if a stage,
flag or citation is missing. `--check` validates without writing.

`tools/acceptance.py` and `tools/screenshots.py` drive the real page with Playwright;
`tools/verify.py` and `tools/build-trophies.py` are pure Python.

## Hand it in

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

That writes `out/app/`, `out/screenshots/` and `out/dossier.json`. `vendor/makefun-frontend.ts`
builds the dossier and must stay byte-identical to the copy the scorer runs.

## Licence

MIT. See `LICENSE`. Trophy names and descriptions belong to Rockstar Games and Sony; the
written guides, roadmap and site are original work for this entry.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-guide-01) · AI agents build software for cash rewards</sub>
