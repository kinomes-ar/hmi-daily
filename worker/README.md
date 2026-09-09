# ADUX Daily — hearts backend (Cloudflare Worker, free tier)

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
| POST   | `/counts` | `{ids:[…]}` (≤200)  | `{counts:{id:n}}`    |
| GET    | `/top`    | `?n=1000`           | `{counts:{id:n}}`    |

`id` = `YYYY-MM-DD-<story number>` (the site's `data-id`); `cid` = a random per-browser id the site generates, so one browser counts once per story.
