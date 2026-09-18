# ADUX Daily — Playbook for the automated run

You are producing **ADUX Daily**, a weekday design digest for the DC Advanced UX (ADUX)
team at Segway-Ninebot. It goes out as a WeCom markdown card and is archived at
https://insight.supermatrix.app (this repository, GitHub Pages). Everything below is the
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
  `https://insight.supermatrix.app/` and confirm it shows today's edition, and finally
  WebFetch `https://www.carscoops.com/`, `https://www.creativeboom.com/` and
  `https://www.yankodesign.com/` and report whether the news sources are reachable
  (if they are not, say so loudly: the environment's network access must be set to Full).
* If a weekday since the last edition was skipped (e.g. an outage), do **not** backfill
  a separate file; just include the strongest stories from those days in today's edition.
* On **Monday**, also produce the weekly summary (Section 7) after the daily edition.

## 1. Editorial brief (what the readers want)

Readers are the **DC Advanced UX team** at Segway-Ninebot. They ship vehicle HMI in the end,
but they are the *advanced* team: they are hired for taste and for what is coming next, so the
edition is weighted toward **experience design, graphics, artistic and motion work, real-time /
game graphics, and new technology** — not toward routine industry news. When two stories are
equally relevant, pick the one that is more beautiful, more crafted, or more technically new.

**Core beats, in priority order**

1. **Car / motorcycle / scooter HMI and cockpit** — clusters, center screens, HUDs,
   physical vs touch controls, steering-wheel switchgear, voice, OS/UI updates, interior
   design, lighting, seats. Tag `Cockpit` (cabin/hardware/interior) or `Interaction`
   (UI, software, controls, OS, gestures, voice).
2. **Micromobility** — e-scooters, e-bikes, motorcycles, helmets and rider gear, their
   displays/apps. Tag `Micromobility`. Segway-Ninebot competitors (Xiaomi, NIU, Yadea,
   Ather, Ola, Gogoro, Bird/Lime) are especially relevant.
3. **Graphics, typography and art direction** — branding/identity, typography, type releases,
   posters, packaging, editorial design, exhibition graphics, artists and illustrators whose
   work a UI designer would steal from. Tag `Visual`. The team loves typography and branding
   deep-dives (e.g. PRINT type reports, Japanese type guides, branding dictionaries) and
   anything genuinely beautiful.
4. **AI in design tools / products** — Figma, Adobe, generative UI, on-device assistants,
   AI-in-car agents, design-tool releases. Tag `AI`.
5. **Product / industrial design & architecture-as-design-thinking** — gadgets, furniture,
   exhibitions, concept objects. Tag `Industrial` (products) or `Design` (vehicles' exterior
   design, design studios, exhibitions, design news in general).
6. **Motion design** — title sequences, brand films and idents, motion identity systems,
   UI/HMI animation reels, kinetic type, 3D/motion studio work, car launch films worth
   studying for their motion language. Tag `Motion`. **Aim for 1–2 per edition** (they count
   inside the Visual quota). Every Motion story must carry a `video` link (Vimeo, YouTube,
   or the studio's own player) so readers can press play.
7. **Real-time / game graphics and new technology** — game art direction and UI (HUDs,
   menus, diegetic interfaces), engine and rendering news (Unreal, Unity, Godot, WebGPU,
   Three.js), shaders and technical art, virtual production, real-time VFX, creative coding
   and generative art, XR / spatial interfaces, and new display, projection, haptics or
   sensing technology shown as a working demo. Tag `Realtime`. **Aim for 2 per edition.**
   Judge these as a designer would: what does it look like, and what does it make possible
   for an interface? Add a `video` link whenever there is a reel or demo to watch. Game
   *business* news (sales, studio layoffs, release dates) is not a story; the art, the tech
   and the interface are.

**Always exclude:** paywalled articles; pure business news (earnings, funding, sales
figures, executive moves); pricing-only or regulation/policy-only stories; recalls; press
releases with no design substance; anything older than ~3 days unless it is an evergreen
deep-dive feature; stories already covered in a previous edition (Section 3).

**Balance per edition (16 stories) — set by the team's reactions.** Readers can heart a story
or mark it "not for me" (eye icon). Before researching, run

```
python3 feedback.py --fetch --brief      # (--fetch needs the Worker; if it fails, run without it)
```

and follow what it prints: the **quota per group** — HMI = Cockpit+Interaction (4),
Micromobility (2), AI (2), Visual = Visual+Motion (4), Realtime (2), Product = Design+Industrial
(2) — moved ±1 by the last three weeks of hearts minus skips, always totalling 16. Also follow
the **sources to favour / deprioritise** and the lists of what the team hearted and skipped —
read those lists for the *kind* of story (subject, depth, angle) to find more of / avoid.
±1 per group is fine when the day is thin, but never fewer than 3 HMI stories or 3 Visual
stories. The rules are printed in `feedback.py`'s docstring; do not invent others.

**Ordering:** item 1 is the lead — the single most important HMI/cockpit story of the day
(fall back to the strongest story of any beat). Then order by importance, but make sure
the strongest Cockpit/Interaction, the strongest AI, and the strongest Visual/Motion/
Realtime/Design story all appear within the first ~6 items — the WeCom card features item 1
plus the first story of each of those groups (`make_card.py`).

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
| Real-time / game / new tech | 80.lv, gamedeveloper.com, artofthetitle.com (game titles), unrealengine.com/news, unity.com/blog, developer.nvidia.com/blog, godotengine.org/news, webkit.org & chrome developers (WebGPU), threejs.org, shadertoy (notable works), siggraph.org, ArtStation blog, Digital Foundry (tech analysis, not reviews), studio sites (Territory Studio, Ash Thorp, Perception, Sarofsky) |
| Motion / video | motionographer.com, stashmedia.tv, artofthetitle.com, itsnicethat.com (animation), creativeboom.com (motion), vimeo.com (Staff Picks — link the Vimeo page), studio sites (buck.co, ordinaryfolk.co, giantant.ca, manvsmachine.com, tendril.ca, dia.tv), brand films on the brand's own YouTube/newsroom |

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
* `blurb` — **one-line EN takeaway, 60–95 characters**, one clause or sentence, no trailing
  period: the single fact a designer should remember (e.g. `No centre screen: a phone clips to a
  rail, an e-paper strip shows climate`). It is what the chat card shows under the title, so
  make it stand on its own.
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
  "blurb": "Twingo E-Tech underneath, squared-off lights and a 10-inch screen for about €19,500",
  "pick": true,
  "zh": "日产确认Pixo——面向欧洲的A级纯电城市小车 ...",
  "ko": "닛산이 유럽용 A세그먼트 전기 시티카 Pixo를 확인했다. ...",
  "src": "Carscoops",
  "url": "https://www.carscoops.com/2026/09/nissan-pixo-ev/",
  "img_url": "https://www.carscoops.com/wp-content/uploads/2026/09/Nissan-Pixo-1024x578.jpg"
 }
]
```

* `tag` ∈ `Cockpit | Interaction | AI | Design | Visual | Motion | Realtime | Industrial | Micromobility`
  (exact spelling, capitalised).
* `pick` — set `"pick": true` on **exactly five** stories: the ones with the most visual and
  brand appeal, the kind the team screenshots and forwards — beautiful UI or graphic work,
  game art and real-time demos, famous brands and studios (Apple, Porsche, Pentagram, Nike,
  Xiaomi, Unreal …), striking cockpit or identity reveals. Not "important" — *desirable to look at*. These five are the chat card;
  spread them across at least three tags. Everything else has no `pick` key.
* `video` (optional, **required for `Motion`**, expected for `Realtime` when a reel exists) — direct link to the playable video (a Vimeo or
  YouTube page, or the studio's own player page). The site shows a play badge and a ▶ Watch
  link; the chat card links it too.
* `img_url` (optional) — pinned lead-image URL; required for carscoops.com,
  motorcycle.com, wardsauto.com items, optional elsewhere. `img_from` (optional) — a
  different page to pull the image from if the original page has none.
* Do **not** add `img` / `img_src`; the GitHub Action fills those in and commits them.
* Only today's file is new. Never rewrite or reformat older data files.

## 6. Build, validate, push (daily)

From the repository root:

```bash
TODAY=$(TZ=Asia/Shanghai date +%F)
python3 feedback.py --fetch --brief            # (already done in step 1 — quotas and source notes)
python3 check_edition.py data/$TODAY.json     # schema, tags, lengths, domains, dedupe
python3 make_card.py $TODAY                   # -> outbox/card.json (must print bytes <= 4096)
python3 build.py standalone                   # regenerates index.html, YYYYMMDD.html, my.html, weekly.html, items.json
git add data/$TODAY.json outbox/card.json likes.json index.html $(echo $TODAY | tr -d -).html my.html weekly.html items.json
git -c user.name=kinomes-ar -c user.email=kinomeartemis@gmail.com commit -m "ADUX Daily $TODAY"
git push origin HEAD:main
```

* `feedback.py --fetch` rewrites `likes.json`; commit it together with the edition (add
  `likes.json` to the `git add` line) so the site's weekly stats stay current.
* Fix every problem `check_edition.py` reports before continuing (it exits non-zero).
* If `make_card.py` says the card is too large, shorten the longest summaries or titles.
* Push **directly to `main`** (all history is authored by kinomes-ar, so the push check
  allows it). Do not create a `claude/...` branch or a pull request unless the push to
  main is refused; in that case push the branch, open a PR titled `ADUX Daily <date>`,
  and say so clearly in your final message.
* After the push, wait ~3 minutes and confirm with WebFetch that
  `https://insight.supermatrix.app/<YYYYMMDD>.html` exists (the Action rebuilds the site).
  If that host is unreachable from the sandbox, confirm instead via the GitHub API
  (`https://api.github.com/repos/kinomes-ar/hmi-daily/actions/runs?per_page=3`) that the
  "Fetch images and rebuild" and "Push card to WeCom" runs succeeded.
  The WeCom card is sent by the other Action automatically; do not send it yourself.
* Never run `cp data/*.json` style bulk copies, never force-push, never amend published
  commits.

## 7. Monday: weekly summary (`weekly/<ISO week>.json`)

On Mondays, after the daily edition is pushed, summarise **last week** (Mon–Fri of the
previous ISO week) from the five `data/` files of that week.

1. Week id = ISO week of last Friday, e.g. `2026-W37`; `from`/`to` = that Monday/Friday.
2. Run `python3 feedback.py --fetch --week <week>` — it prints JSON with the week's reaction
   stats per category and source, `top` (most hearted), `skipped` (most "not for me"),
   `next_quotas` and `quota_notes` (what the rule decided for next week), `favour` /
   `deprioritise` sources. Read the five data files for the content itself. Hearts = what the
   team loved, skips = what it does not want more of.
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
 "top": [{"id": "2026-09-10-4", "n": 2}, {"id": "2026-09-08-5", "n": 1}],
 "feedback": {
   "skipped": [{"id": "2026-09-10-15", "n": 2}],
   "actions": {"en": "...", "zh": "...", "ko": "..."}
 }
}
```

   * `title`: one editorial line naming the week's 2–3 defining stories (each language).
   * `intro`: 80–130 words EN (and equivalents) — the week's arc, the most-hearted item,
     and the cross-beat theme.
   * One `cats` entry per tag that had stories, in the order above; each `en` 60–110 words
     naming companies, products and what specifically was talked about, plus `items`
     (the ids of the stories it refers to, 3–8 each). `zh`/`ko` are equivalents.
   * `top`: hearts ranked, up to 5, only n>0 — copy from `feedback.py --week`.
   * `feedback.skipped`: the `skipped` list from `feedback.py --week` (up to 5, only n>0).
   * `feedback.actions`: 2–4 sentences per language that (a) say what the team hearted and
     skipped this week, in plain words (categories, kinds of story, sources), (b) state the
     concrete consequence for next week — the `next_quotas` numbers and any source that is
     favoured or deprioritised, quoting `quota_notes` — and (c) if reactions were too few to
     move anything, say so and that base quotas apply. Same facts in EN / 中 / 한. This text is
     shown on the weekly page and in the Monday card, so it must be honest and specific.
   * Also mention the most-hearted and most-skipped story in `intro`.
   The site computes the per-category / per-source tables itself from `likes.json`; you only
   write the words.
4. Build and push:

```bash
python3 make_weekly_card.py <week>            # -> outbox/card.json (<= 4096 bytes)
python3 build.py standalone
printf '\n' >> data/<last Friday>.json         # touches a data file so the rebuild Action runs
git add weekly/<week>.json likes.json outbox/card.json weekly.html index.html items.json data/<last Friday>.json
git -c user.name=kinomes-ar -c user.email=kinomeartemis@gmail.com commit -m "ADUX Weekly <week>"
git push origin HEAD:main
```

## 8. Final message of the run

End with a short trilingual report (EN / 中 / 한, three lines each at most): edition date,
number of stories, the quotas used (from `feedback.py`), the five featured titles, anything
skipped or degraded (e.g. a source
unreachable, an image pinned manually, a PR opened instead of a direct push). If nothing
could be published, say exactly which step failed and what was tried.
