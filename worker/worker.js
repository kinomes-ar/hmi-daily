/**
 * ADUX Daily — shared heart counts.
 * Cloudflare Worker + one KV namespace bound as `LIKES`.
 *
 *   POST /like    {id, on, cid}  -> {id, count}     toggle one heart for one client
 *   POST /counts  {ids:[...]}    -> {counts:{id:n}} counts for up to 200 ids
 *   GET  /top?n=1000             -> {counts:{id:n}} every id with a count (site build snapshot)
 *   GET  /                       -> ok
 *
 * Keys:  c:<id>        running count
 *        v:<cid>:<id>  "1" while this client has the heart on (prevents double counting)
 */

const ORIGINS = ["https://hmi.supermatrix.app", "http://localhost", "http://127.0.0.1"];
const ID_RE = /^\d{4}-\d{2}-\d{2}-\d{1,2}$/;
const CID_RE = /^[a-z0-9]{8,40}$/;

function cors(req) {
  const o = req.headers.get("Origin") || "";
  const ok = ORIGINS.some((x) => o === x || o.startsWith(x + ":"));
  return {
    "Access-Control-Allow-Origin": ok ? o : ORIGINS[0],
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Cache-Control": "no-store",
    "Content-Type": "application/json; charset=utf-8",
  };
}

const json = (req, body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: cors(req) });

async function getCount(env, id) {
  const v = await env.LIKES.get("c:" + id);
  return v ? parseInt(v, 10) || 0 : 0;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req) });

    if (req.method === "GET" && url.pathname === "/") return json(req, { ok: true });

    if (req.method === "GET" && url.pathname === "/top") {
      const n = Math.min(parseInt(url.searchParams.get("n") || "1000", 10) || 1000, 1000);
      const list = await env.LIKES.list({ prefix: "c:", limit: n });
      const counts = {};
      // read in batches so a big archive never trips the subrequest limit
      const keys = list.keys.map((k) => k.name);
      for (let i = 0; i < keys.length; i += 50) {
        const vals = await Promise.all(keys.slice(i, i + 50).map((k) => env.LIKES.get(k)));
        vals.forEach((v, j) => {
          const c = parseInt(v || "0", 10) || 0;
          if (c > 0) counts[keys[i + j].slice(2)] = c;
        });
      }
      return json(req, { counts });
    }

    if (req.method !== "POST") return json(req, { error: "method" }, 405);

    let body;
    try { body = await req.json(); } catch { return json(req, { error: "json" }, 400); }

    if (url.pathname === "/counts") {
      const ids = Array.isArray(body.ids) ? body.ids.filter((x) => ID_RE.test(x)).slice(0, 200) : [];
      const vals = await Promise.all(ids.map((id) => getCount(env, id)));
      const counts = {};
      ids.forEach((id, i) => { if (vals[i] > 0) counts[id] = vals[i]; });
      return json(req, { counts });
    }

    if (url.pathname === "/like") {
      const { id, on, cid } = body;
      if (!ID_RE.test(id || "") || !CID_RE.test(cid || "")) return json(req, { error: "bad id" }, 400);
      const vkey = "v:" + cid + ":" + id;
      const had = (await env.LIKES.get(vkey)) === "1";
      let count = await getCount(env, id);
      if (on && !had) {
        count += 1;
        await Promise.all([env.LIKES.put(vkey, "1"), env.LIKES.put("c:" + id, String(count))]);
      } else if (!on && had) {
        count = Math.max(0, count - 1);
        await Promise.all([env.LIKES.delete(vkey), env.LIKES.put("c:" + id, String(count))]);
      }
      return json(req, { id, count });
    }

    return json(req, { error: "not found" }, 404);
  },
};
