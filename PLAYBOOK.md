# ADUX Daily — Playbook for the automated run

You are producing **ADUX Daily**, a weekday design digest for the DC Advanced UX (ADUX)
team at Segway-Ninebot. It goes out as a WeCom markdown card and is archived at
https://hmi.supermatrix.app (this repository, GitHub Pages). Everything below is the
complete procedure. Work autonomously, do not ask questions, finish with a push to `main`.

Everything in this repo is already wired: pushing `data/<date>.json` triggers
`.github/workflows/publish.yml` (image fetch + site rebuild) and pushing
`outbox/card.json` triggers `.github/workflows/wecom.yml` (WeCom webhook). **Your only
job is to research, write, validate, and push.** Never touch the workflow files, secrets,
`likes.json`, `assets/`, or `CNAME`.

---

## 0. Date and scope

* The edition date is **today in Asia/Shanghai (UTC+8)**: `TZ=Asia/Shanghai date +%F`.
* Weekdays only (Mon–Fri). If it is Saturday/Sunday, stop and do nothing.
* If `data/<today>.json` already exists in the repo, the edition was already published.
  Do not write anything; instead run the **self-check** and report its result:
  `python3 check_edition.py data/<today>.json`, then `git push --dry-run origin HEAD:main`
  (this proves the push credential works without changing the repo), then WebFetch
  `https://hmi.supermatrix.app/` and confirm it shows today's edition.
* If a weekday since the last edition was skipped (e.g. an outage), do **not** backfill
  a separate file; just include the strongest stories from those days in today's edition.
* On **Monday**, also produce the weekly summary (Section 7) after the daily edition.

## 1. Editorial brief (what the readers want)

Readers are automotive & micromobility HMI/UX designers and graphic designers.

**Core beats, in priority order**

1. **Car / motorcycle / scooter HMI and cockpit** — clusters, center screens, HUDs,
   physical vs touch controls, steering-wheel switchgear, voice, OS/UI updates, interior
   design, lighting, seats. Tag `Cockpit` (cabin/hardware/interior) or `Interaction`
   (UI, software, controls, OS, gestures, voice).
2. **Micromobility** — e-scooters, e-bikes, motorcycles, helmets and rider gear, their
   displays/apps. Tag `Micromobility`. Segway-Ninebot competitors (Xiaomi, NIU, Yadea,
   Ather, Ola, Gogoro, Bird/Lime) are especially relevant.
3. **2D graphic design** — branding/identity, typography, type releases, posters, packaging,
   editorial design, motion graphics. Tag `Visual`. The team loves typography and branding
   deep-dives (e.g. PRINT type reports, Japanese type guides, branding dictionaries).
4. **AI in design tools / products** — Figma, Adobe, generative UI, on-device assistants,
   AI-in-car agents, design-tool releases. Tag `AI`.
5. **Product / industrial design & architecture-as-design-thinking** — gadgets, furniture,
   exhibitions, concept objects. Tag `Industrial` (products) or `Design` (vehicles' exterior
   design, design studios, exhibitions, design news in general).

**Always exclude:** paywalled articles; pure business news (earnings, funding, sales
figures, executive moves); pricing-only or regulation/policy-only stories; recalls; press
releases with no design substance; anything older than ~3 days unless it is an evergreen
deep-dive feature; stories already covered in a previous edition (Section 3).

**Balance per edition (16 stories):** roughly 3–4 Cockpit/Interaction, 1–2 Micromobility,
1–2 AI, 4–5 Visual, 3–4 Design/Industrial. Adjust to what the day actually offers, but
never fewer than 2 HMI stories and 3 Visual stories.

**Ordering:** item 1 is the lead — the single most important HMI/cockpit story of the day
(fall back to the strongest story of any beat). Then order by importance, but make sure
the strongest Cockpit/Interaction, the strongest AI, and the strongest Visual/Design/
Industrial story all appear within the first ~6 items — the card features item 1 plus the
first story of each of those groups (`make_card.py`).

## 2. Sources

Only link to the **original publisher** on these domains (the `url` field). Never link
aggregators, syndications, Google News, MSN, Yahoo, guideautoweb, newsbreak, etc.

| Beat | Sources (fetch their front/category pages) |
| --- | --- |
| Car HMI / cockpit / design | carscoops.com, carnewschina.com, insideevs.com, motor1.com, cardesignnews.com, automotiveinteriorsworld.com, wardsauto.com, autoblog.com, electrek.co, autodesignmagazine.com, brand newsrooms (media.*.com, press.*.com) |
| Motorcycle / micromobility | motorcycle.com, cycleworld.com, rideapart.com, electrek.co (e-bike/scooter), electricscooterguide.com, brand newsrooms |
| Graphic / branding / type | creativeboom.com, printmag.com, itsnicethat.com, designboom.com (design/art), dezeen.com (design), brandnew (underconsideration.com/brandnew — only if not paywalled that day) |
| Product / industrial | yankodesign.com, designboom.com (technology/design), dezeen.com, core77.com |
| AI / tools | figma.com/blog, figma release notes (releasebot.io/updates/figma), adobe.com/blog, theverge.com (design/AI tool stories only), yankodesign.com tech |

**How to read the web from the cloud session:** use the `WebFetch` tool (and `WebSearch`
for discovery). Plain `curl`/`python requests` to news sites is blocked by the sandbox
network policy — do not fight it, use WebFetch. GitHub is reachable normally for git.

Fetch tips learned the hard way:

* `designboom.com` often fails in WebFetch with "Too many redirects". Keep the designboom
  URL as `url`, but read the text from a syndication (search the title; freeyork.org and
  similar mirror it) or from designboom's RSS `https://www.designboom.com/feed/`.
* `carscoops.com`, `motorcycle.com`, `wardsauto.com` are bot-walled for the image fetcher.
  For those, ask WebFetch for the article's `og:image` / main image URL and pin it in
  `img_url` (see schema). For motorcycle.com use the *actual* body `<img src>` including
  its query string (e.g. `...jpg?size=720x845&nocrop=1`); guessed URLs 404.
* Category pages worth a first pass: `carscoops.com/category/news/`, `carnewschina.com`,
  `motorcycle.com/news`, `creativeboom.com/inspiration/` and `/news/`, `printmag.com`,
  `yankodesign.com`, `designboom.com/design/`, `designboom.com/technology/`,
  `itsnicethat.com/news`, `dezeen.com/design/`, `cardesignnews.com`.
* WebSearch is good for "past 24 hours" sweeps: e.g. `site:carscoops.com interior screen`,
  `"cluster" OR "infotainment" 2026`, `rebrand identity typeface new`, `e-scooter display`.

Aim to skim 12+ listing pages and open ~30 candidate articles to end up with 16 good ones.

## 3. Deduplication

Before choosing stories, load the URLs and titles of the last 15 editions:

```
python3 check_edition.py --recent
```

Skip any candidate whose URL is already used, and any story that is the *same news* as a
past item even from another outlet (e.g. the same concept car covered by two sites).
Follow-ups are fine only if there is substantive new information (a production version
after a concept, hands-on after a reveal) — say so in the summary.

## 4. Writing

Each story has an English title and a summary in three languages: **EN → 中文 (简体) →
한국어**. Write like a sharp design editor, not a press release. Lead with the design
detail a designer would want to know (sizes, layouts, what changed, why it matters);
include concrete specs (screen inches, resolution, materials, typeface names, dates).
No hype adjectives, no "revolutionary". Do not moralise. Never mention "our team".

* `t` — English title, 25–58 characters, headline style, usually `Subject: hook`
  (e.g. `Nissan Pixo: a Twingo in a boxier suit`, `Form hides two logos inside one typeface`).
* `en` — 2–4 sentences, 280–520 characters. Facts first, then a one-clause design read.
* `zh` — natural Simplified Chinese, 90–200 characters, same facts (not a word-for-word
  translation; write it as a Chinese editor would). Use full-width punctuation.
* `ko` — natural Korean in 문어체 (‑다/‑했다 endings), 120–260 characters, same facts.
  Use standard Korean spellings of brand names (닛산, 아우디, 샤오미, 리오토 …).
* `src` — publisher display name (`Carscoops`, `CarNewsChina`, `Creative Boom`,
  `designboom`, `Yanko Design`, `PRINT Magazine`, `Motorcycle.com`, `Car Design News`…).
* Keep numbers, model names, typeface names identical across languages.

## 5. Data file schema — `data/YYYY-MM-DD.json`

A JSON array of exactly 16 objects, in publication order, `ensure_ascii=False`, indent 1:

```json
[
 {
  "tag": "Cockpit",
  "t": "Nissan Pixo: a Twingo in a boxier suit",
  "en": "Nissan has confirmed the Pixo, an A-segment electric city car ...",
  "zh": "日产确认Pixo——面向欧洲的A级纯电城市小车 ...",
  "ko": "닛산이 유럽용 A세그먼트 전기 시티카 Pixo를 확인했다. ...",
  "src": "Carscoops",
  "url": "https://www.carscoops.com/2026/09/nissan-pixo-ev/",
  "img_url": "https://www.carscoops.com/wp-content/uploads/2026/09/Nissan-Pixo-1024x578.jpg"
 }
]
```

* `tag` ∈ `Cockpit | Interaction | AI | Design | Visual | Industrial | Micromobility`
  (exact spelling, capitalised).
* `img_url` (optional) — pinned lead-image URL; required for carscoops.com,
  motorcycle.com, wardsauto.com items, optional elsewhere. `img_from` (optional) — a
  different page to pull the image from if the original page has none.
* Do **not** add `img` / `img_src`; the GitHub Action fills those in and commits them.
* Only today's file is new. Never rewrite or reformat older data files.

## 6. Build, validate, push (daily)

From the repository root:

```bash
TODAY=$(TZ=Asia/Shanghai date +%F)
python3 check_edition.py data/$TODAY.json     # schema, tags, lengths, domains, dedupe
python3 make_card.py $TODAY                   # -> outbox/card.json (must print bytes <= 4096)
python3 build.py standalone                   # regenerates index.html, YYYYMMDD.html, my.html, weekly.html, items.json
git add data/$TODAY.json outbox/card.json index.html $(echo $TODAY | tr -d -).html my.html weekly.html items.json
git -c user.name=kinomes-ar -c user.email=kinomeartemis@gmail.com commit -m "ADUX Daily $TODAY"
git push origin HEAD:main
```

* Fix every problem `check_edition.py` reports before continuing (it exits non-zero).
* If `make_card.py` says the card is too large, shorten the longest summaries or titles.
* Push **directly to `main`** (all history is authored by kinomes-ar, so the push check
  allows it). Do not create a `claude/...` branch or a pull request unless the push to
  main is refused; in that case push the branch, open a PR titled `ADUX Daily <date>`,
  and say so clearly in your final message.
* After the push, wait ~3 minutes and confirm with WebFetch that
  `https://hmi.supermatrix.app/<YYYYMMDD>.html` exists (the Action rebuilds the site).
  The WeCom card is sent by the other Action automatically; do not send it yourself.
* Never run `cp data/*.json` style bulk copies, never force-push, never amend published
  commits.

## 7. Monday: weekly summary (`weekly/<ISO week>.json`)

On Mondays, after the daily edition is pushed, summarise **last week** (Mon–Fri of the
previous ISO week) from the five `data/` files of that week.

1. Week id = ISO week of last Friday, e.g. `2026-W37`; `from`/`to` = that Monday/Friday.
2. Read the five data files and `likes.json` (`counts` keyed by item id
   `YYYY-MM-DD-N`, N is 1-based position in the day's file). Hearts = what the team loved.
3. Write `weekly/<week>.json`:

```json
{
 "week": "2026-W37", "from": "2026-09-07", "to": "2026-09-11",
 "title": {"en": "...", "zh": "...", "ko": "..."},
 "intro": {"en": "...", "zh": "...", "ko": "..."},
 "cats": [
   {"tag": "Cockpit", "en": "...", "zh": "...", "ko": "...", "items": ["2026-09-08-1", "2026-09-10-1"]},
   {"tag": "Interaction", ...}, {"tag": "AI", ...}, {"tag": "Micromobility", ...},
   {"tag": "Visual", ...}, {"tag": "Design", ...}, {"tag": "Industrial", ...}
 ],
 "top": [{"id": "2026-09-10-4", "n": 2}, {"id": "2026-09-08-5", "n": 1}]
}
```

   * `title`: one editorial line naming the week's 2–3 defining stories (each language).
   * `intro`: 80–130 words EN (and equivalents) — the week's arc, the most-hearted item,
     and the cross-beat theme.
   * One `cats` entry per tag that had stories, in the order above; each `en` 60–110 words
     naming companies, products and what specifically was talked about, plus `items`
     (the ids of the stories it refers to, 3–8 each). `zh`/`ko` are equivalents.
   * `top`: hearts ranked, up to 5, only n>0.
4. Build and push:

```bash
python3 make_weekly_card.py <week>            # -> outbox/card.json (<= 4096 bytes)
python3 build.py standalone
printf '\n' >> data/<last Friday>.json         # touches a data file so the rebuild Action runs
git add weekly/<week>.json outbox/card.json weekly.html index.html items.json data/<last Friday>.json
git -c user.name=kinomes-ar -c user.email=kinomeartemis@gmail.com commit -m "ADUX Weekly <week>"
git push origin HEAD:main
```

## 8. Final message of the run

End with a short trilingual report (EN / 中 / 한, three lines each at most): edition date,
number of stories, the five featured titles, anything skipped or degraded (e.g. a source
unreachable, an image pinned manually, a PR opened instead of a direct push). If nothing
could be published, say exactly which step failed and what was tried.
