# news-image-20261122-v2

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/sixthin016/news-image-20261122-v2/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/sixthin016/news-image-20261122-v2/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

A one-page Sunday broadsheet that sums up the world news of **Sunday, 22 November 2026** in a single 1024×1024 image.

The lead story is Iran striking U.S. bases in the Gulf (Bahrain, 04:26 UTC), followed by a 4×9 grid of **36 more illustrated stories — 37 featured in total** — plus a numbered **"ALSO ON SUNDAY"** list of 24 further items, a first-wire UTC timeline of 10 events (00:37–06:58), a world map with **37 numbered pins** (gold star = lead), and region chips for **7 regions** (M. East 3, Europe 10, N. America 7, LatAm 2, Asia 6, Africa 4, Sport 5).

Every featured story happened on, or was first reported on, Sunday 22 November 2026, checked against that day's wire digests (Reuters / AP / BBC / AFP / Al Jazeera) plus live search the same day. Each card carries its source wire code. A **DATE CHECK** box names what was deliberately left out and why: the Peru quake, the EU–Indonesia trade deal and the Poland missiles were all first filed on 21 November, so they are held out of the grid and named there instead.

The image is produced by a deterministic Python generator (`main.py`): pure standard library (math / os / struct / zlib), no network, no randomness, no wall-clock time — two runs produce byte-identical output. This is the v3-fix reflow: the earlier v3 broadsheet was 1024×1400, a fatal breach of the competition's hard 1024×1024 limit, so the grid was reflowed to 4 columns × 9 rows with smaller cards and scaled-down scenes, keeping every story.

## Run it

```sh
python3 main.py
```

This writes the entry to `output/entry.png` (1024×1024, ~303 KB). Set `MAKEFUN_OUTPUT_DIR` to write it elsewhere instead — the grader path is `$MAKEFUN_OUTPUT_DIR/entry.png`. Rendering takes about 7–8 seconds. No third-party packages are needed; Python 3 with the standard library is enough.

Verify a fresh render is byte-identical to the checked-in one:

```sh
sha256sum output/entry.png
# 0e03dd66ba28ac711fe81aa78372343e23d0876ac75dac70c853a3d2603bb6d0
```

## Contents

- `main.py` — the deterministic broadsheet generator (canvas, 5×7 bitmap font, PNG writer, 32 illustrated mini-scenes, world map, layout)
- `output/entry.png` — the generated entry (1024×1024)
- `VERIFY-v3.md` — verification notes for the v3-fix reflow (determinism check, consistency audit, visual inspection)
- `LICENSE` — license

<sub>Entered on [make.fun](https://make.fun/?ref=wffmhs5a&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
