/**
 * ADUX Daily — shared reactions (hearts + "not for me").
 * Cloudflare Worker + one KV namespace bound as `LIKES`.
 *
 *   POST /like    {id, on, cid}  -> {id, count}            toggle one heart for one client
 *   POST /skip    {id, on, cid}  -> {id, count}            toggle one "not for me" for one client
 *   POST /counts  {ids:[...]}    -> {counts:{id:n}, skips:{id:n}}   for up to 200 ids
 *   GET  /top?n=1000             -> {counts:{id:n}, skips:{id:n}}   every id with a count (site build snapshot)
 *   GET  /                       -> ok
 *
 * Keys:  c:<id>        running heart count        v:<cid>:<id>  "1" while this client's heart is on
 *        s:<id>        running skip count         w:<cid>:<id>  "1" while this client's skip is on
 * A client is either hearting or skipping a story, never both: turning one on clears the other.
 */

const ORIGINS = ["https://hmi.supermatrix.app", "http://localhost", "http://127.0.0.1"];
const ID_RE = /^\d{4}-\d{2}-\d{2}-\d{1,2}$/;
const CID_RE = /^[a-z0-9]{8,40}$/;

const KINDS = {
  like: { c: "c:", v: "v:" },
  skip: { c: "s:", v: "w:" },
};

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

async function getNum(env, key) {
  const v = await env.LIKES.get(key);
  return v ? parseInt(v, 10) || 0 : 0;
}

async function listCounts(env, prefix, n) {
  const list = await env.LIKES.list({ prefix, limit: n });
  const out = {};
  const keys = list.keys.map((k) => k.name);
  // read in batches so a big archive never trips the subrequest limit
  for (let i = 0; i < keys.length; i += 50) {
    const vals = await Promise.all(keys.slice(i, i + 50).map((k) => env.LIKES.get(k)));
    vals.forEach((v, j) => {
      const c = parseInt(v || "0", 10) || 0;
      if (c > 0) out[keys[i + j].slice(prefix.length)] = c;
    });
  }
  return out;
}

/** Toggle `kind` for (cid, id). Returns the new count of that kind. */
async function toggle(env, kind, id, cid, on) {
  const k = KINDS[kind];
  const vkey = k.v + cid + ":" + id;
  const had = (await env.LIKES.get(vkey)) === "1";
  let count = await getNum(env, k.c + id);
  if (on && !had) {
    count += 1;
    await Promise.all([env.LIKES.put(vkey, "1"), env.LIKES.put(k.c + id, String(count))]);
  } else if (!on && had) {
    count = Math.max(0, count - 1);
    await Promise.all([env.LIKES.delete(vkey), env.LIKES.put(k.c + id, String(count))]);
  }
  return count;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req) });

    if (req.method === "GET" && url.pathname === "/") return json(req, { ok: true, v: 2 });

    if (req.method === "GET" && url.pathname === "/top") {
      const n = Math.min(parseInt(url.searchParams.get("n") || "1000", 10) || 1000, 1000);
      const [counts, skips] = await Promise.all([listCounts(env, "c:", n), listCounts(env, "s:", n)]);
      return json(req, { counts, skips });
    }

    if (req.method !== "POST") return json(req, { error: "method" }, 405);

    let body;
    try { body = await req.json(); } catch { return json(req, { error: "json" }, 400); }

    if (url.pathname === "/counts") {
      const ids = Array.isArray(body.ids) ? body.ids.filter((x) => ID_RE.test(x)).slice(0, 200) : [];
      const [likes, skips] = await Promise.all([
        Promise.all(ids.map((id) => getNum(env, "c:" + id))),
        Promise.all(ids.map((id) => getNum(env, "s:" + id))),
      ]);
      const counts = {}, sk = {};
      ids.forEach((id, i) => { if (likes[i] > 0) counts[id] = likes[i]; if (skips[i] > 0) sk[id] = skips[i]; });
      return json(req, { counts, skips: sk });
    }

    if (url.pathname === "/like" || url.pathname === "/skip") {
      const kind = url.pathname === "/like" ? "like" : "skip";
      const other = kind === "like" ? "skip" : "like";
      const { id, on, cid } = body;
      if (!ID_RE.test(id || "") || !CID_RE.test(cid || "")) return json(req, { error: "bad id" }, 400);
      if (on) await toggle(env, other, id, cid, false); // mutually exclusive per client
      const count = await toggle(env, kind, id, cid, !!on);
      return json(req, { id, count, kind });
    }

    return json(req, { error: "not found" }, 404);
  },
};
