# ADUX Daily — reactions backend (hearts + "not for me") (Cloudflare Worker, free tier)

One-time setup, ~5 minutes, all in the Cloudflare dashboard. No CLI, no token.

1. **Create a KV namespace**
   Cloudflare dashboard → *Storage & Databases* → *KV* → **Create a namespace** → name it `adux-likes`.

2. **Create the Worker**
   *Compute (Workers)* → *Workers & Pages* → **Create** → *Start with Hello World!* → name it `adux-likes` → **Deploy**.

3. **Paste the code**
   On the new Worker → **Edit code** → replace everything in `worker.js` with the contents of this folder's `worker.js` → **Deploy**.

4. **Bind the KV namespace**
   Worker → *Settings* → *Bindings* → **Add** → *KV namespace* →
   Variable name **`LIKES`** (exactly) → select `adux-likes` → **Deploy**.

5. **Copy the URL**
   The Worker's address looks like `https://adux-likes.<your-subdomain>.workers.dev`.
   Open it once in a browser — it should answer `{"ok":true}`.
   Then put that URL into `site.json` in this repo:

   ```json
   {"like_api": "https://adux-likes.<your-subdomain>.workers.dev"}
   ```

   (or just paste the URL into the chat and Claude will commit it.)

That's it. Hearts on the site start syncing on the next rebuild.

## Limits (free plan)
- 100,000 requests/day, 1,000 KV writes/day, 100,000 KV reads/day — far above a team's usage.
- Counts are best-effort (KV is eventually consistent); two hearts in the same millisecond may merge. Fine for a newsletter.

## Endpoints
| Method | Path      | Body / query        | Returns              |
|--------|-----------|---------------------|----------------------|
| POST   | `/like`   | `{id, on, cid}`     | `{id, count}`        |
| POST   | `/skip`   | `{id, on, cid}`     | `{id, count}`  ("not for me"; clears that client's heart) |
| POST   | `/counts` | `{ids:[…]}` (≤200)  | `{counts:{id:n}, skips:{id:n}}` |
| GET    | `/top`    | `?n=1000`           | `{counts:{id:n}, skips:{id:n}}` |
| GET    | `/feishu/preview` | `?date=` or `?week=` | the Feishu card JSON (no send) |
| GET    | `/feishu/status`  |                     | what was sent today            |

## Feishu (Lark) delivery
The same Worker posts the daily card to a Feishu group by itself — no GitHub secrets, no Mac.
1. Feishu group → Settings → Bots → Add bot → **Custom bot** → name `ADUX Daily` → turn on
   **Signature verification** → copy the **Webhook URL** and the **Secret**.
2. Worker → *Settings* → *Variables and Secrets* → add **Secret** `FEISHU_WEBHOOK` (the URL) and
   **Secret** `FEISHU_SECRET` (the signing secret) → Deploy.
3. Worker → *Settings* → *Triggers* → *Cron Triggers* → **Add** → expression `*/30 2-9 * * 1-5`
   (every 30 min, 10:00–17:59 Beijing, weekdays) → Save.
Each tick sends today's edition once it is on the site (KV key `sent:<date>` prevents repeats);
on Mondays it also sends last week's weekly card (`sentw:<week>`).
Cloudflare's cron uses 1 = Sunday for the day-of-week field, so write weekdays as `MON-FRI`
(`*/30 2-9 * * MON-FRI`), not `1-5`. Check the "Next" time it shows: it must land on a weekday.

## Publishing by hand
Add one more **Secret** `PUBLISH_KEY` with a word you will remember, then open
`https://<worker>/publish` — type the key once (it is kept in that browser) and press
**Publish this edition**. It sends only what has not gone out yet; **Send again (force)**
re-sends, **Publish weekly** sends last week's roundup, **Preview only** shows the card JSON.
Check: `https://<worker>/feishu/status` and `https://<worker>/feishu/preview?date=YYYY-MM-DD`.

## Updating the Worker
Paste the new `worker.js` over the old one (Worker → **Edit code** → replace all → **Deploy**).
Existing heart counts are kept; skips use separate keys (`s:`/`w:`).

`id` = `YYYY-MM-DD-<story number>` (the site's `data-id`); `cid` = a random per-browser id the site generates, so one browser counts once per story.
