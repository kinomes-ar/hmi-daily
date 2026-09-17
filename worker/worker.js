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
 *
 * ---- Feishu (Lark) delivery, driven by a Cron Trigger ----
 *   Cron  "30-minute ticks, 02:00-09:59 UTC, Mon-Fri" (expression: every 30 min 2-9 UTC weekdays)  every 30 min, 10:00-17:59 Beijing, weekdays
 *   Each tick: if data/<today>.json exists on the site and "sent:<today>" is not in KV,
 *   build a compact interactive card (the five picks: title link + one-line EN blurb; the
 *   site carries all 16 stories in three languages) and POST it to the Feishu webhook. On Mondays
 *   the previous ISO week's weekly/<week>.json is sent the same way ("sentw:<week>").
 *   Secrets (Worker → Settings → Variables and Secrets):
 *     FEISHU_WEBHOOK  https://open.feishu.cn/open-apis/bot/v2/hook/...
 *     FEISHU_SECRET   the bot's signing secret (optional; leave unset if signing is off)
 *   GET /feishu/preview?date=YYYY-MM-DD   returns the card JSON (no sending), for checks
 *   GET /feishu/preview?week=YYYY-Www     same for the weekly card
 */

const SITE = "https://hmi.supermatrix.app";
const NUM = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳";
const GROUPS = [["cockpit", "interaction"], ["ai"], ["design", "visual", "industrial", "motion"]];
const CARD_LIMIT = 28000; // bytes of card JSON; Feishu caps interactive cards around 30 KB

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

// ---------------------------------------------------------------- Feishu card
function beijingDate(d = new Date()) {
  return new Date(d.getTime() + 8 * 3600 * 1000).toISOString().slice(0, 10);
}
function beijingWeekday(d = new Date()) {
  return new Date(d.getTime() + 8 * 3600 * 1000).getUTCDay(); // 0 Sun .. 6 Sat
}
function isoWeekOf(dateStr) {
  const d = new Date(dateStr + "T00:00:00Z");
  const day = (d.getUTCDay() + 6) % 7; // Mon = 0
  d.setUTCDate(d.getUTCDate() - day + 3); // Thursday of this week
  const y = d.getUTCFullYear();
  const jan4 = new Date(Date.UTC(y, 0, 4));
  const wk = 1 + Math.round(((d - jan4) / 86400000 - 3 + ((jan4.getUTCDay() + 6) % 7)) / 7);
  return y + "-W" + String(wk).padStart(2, "0");
}
function prevWeekId(todayStr) {
  const d = new Date(todayStr + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() - 7);
  return isoWeekOf(d.toISOString().slice(0, 10));
}

async function siteJson(path) {
  const r = await fetch(SITE + "/" + path + "?t=" + Date.now(), { headers: { "Cache-Control": "no-cache" } });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error("site " + r.status + " for " + path);
  return r.json();
}

function pickFeatured(items, n = 5) {
  const feats = items.length ? [0] : [];
  for (const g of GROUPS) {
    for (let i = 0; i < items.length; i++) {
      if (feats.includes(i)) continue;
      if (g.includes(String(items[i].tag || "").trim().toLowerCase())) { feats.push(i); break; }
    }
    if (feats.length >= n) break;
  }
  for (let i = 0; feats.length < Math.min(n, items.length); i++) if (!feats.includes(i)) feats.push(i);
  return feats.sort((a, b) => a - b);
}

// The chat card shows the five stories with the most visual / brand appeal — the kind the team
// screenshots: beautiful UI and graphic work, famous brands and studios. The routine marks them
// with "pick": true; older editions fall back to a taste heuristic.
const TAG_W = { motion: 3.2, visual: 3, interaction: 3, cockpit: 2.5, design: 2, ai: 2, micromobility: 1.5, industrial: 1 };
const BRANDS = /\b(apple|iphone|ipad|google|pixel|samsung|sony|nintendo|nike|adidas|ikea|lego|porsche|ferrari|lamborghini|bmw|mercedes|audi|volkswagen|vw|tesla|rivian|lucid|polestar|volvo|rolls-royce|bentley|aston martin|jaguar|land rover|range rover|hyundai|kia|genesis|toyota|lexus|honda|nissan|mazda|xiaomi|huawei|byd|nio|xpeng|li auto|zeekr|ducati|honda|yamaha|kawasaki|harley|segway|ninebot|figma|adobe|canva|pentagram|dieter rams|jony ive|lovefrom|openai|dyson|leica|braun|muji|teenage engineering|nothing)\b/i;
const PRETTY_SRC = /creative boom|it's nice that|designboom|print|dezeen|car design news|yanko|motionographer|stash|art of the title|vimeo/i;

function pickCard(items, n = 5) {
  const marked = items.map((it, i) => [it, i]).filter(([it]) => it.pick === true).map(([, i]) => i);
  if (marked.length) return marked.slice(0, n);
  const scored = items.map((it, i) => {
    const tag = String(it.tag || "").toLowerCase();
    const text = (it.t || "") + " " + (it.src || "");
    let s = (TAG_W[tag] || 1) + (16 - i) / 16;
    if (BRANDS.test(text)) s += 1.5;
    if (PRETTY_SRC.test(it.src || "")) s += 0.8;
    return { i, s, tag };
  }).sort((a, b) => b.s - a.s);
  const out = [], perTag = {};
  for (const x of scored) {
    if ((perTag[x.tag] || 0) >= 2) continue;
    out.push(x.i); perTag[x.tag] = (perTag[x.tag] || 0) + 1;
    if (out.length >= n) break;
  }
  return out.sort((a, b) => a - b);
}

function clip(s, max) {
  s = String(s || "");
  if (s.length <= max) return s;
  let out = s.slice(0, max);
  const m = out.match(/^[\s\S]*[。．.!?！？…](?!\d)/);
  if (m && m[0].length >= max * 0.45) return m[0];
  return out.replace(/[\s,、，—-]+$/, "") + "…";
}

function md(s) {
  // keep Feishu markdown from misreading titles
  return String(s || "").replace(/\[/g, "［").replace(/\]/g, "］");
}

function reactions(counts, skips, id) {
  const l = counts[id] || 0, s = skips[id] || 0;
  const parts = [];
  if (l) parts.push("❤" + l);
  if (s) parts.push("✕" + s);
  return parts.length ? "  " + parts.join(" ") : "";
}

function firstSentence(s, max) {
  s = String(s || "").trim();
  const m = s.match(/^[\s\S]*?[.!?](?=\s|$)/);
  let one = m && m[0].length >= 40 ? m[0] : s;
  if (one.length <= max) return one;
  // too long for one line: cut at the last clause boundary, else at a word
  const head = one.slice(0, max);
  let best = -1;
  for (const sep of [", ", "; ", " — ", ": ", " – "]) {
    const p = head.lastIndexOf(sep);
    if (p > best) best = p;
  }
  if (best >= max * 0.55) return head.slice(0, best).replace(/[\s,;:—–-]+$/, "") + "…";
  const w = head.lastIndexOf(" ");
  return head.slice(0, w > max * 0.6 ? w : max).replace(/[\s,;:—–-]+$/, "") + "…";
}

function blurb(it, cap) {
  // one-line takeaway: the routine writes `blurb` (EN, <= 90 chars); older editions fall back to the first sentence
  return it.blurb ? clip(it.blurb, cap) : firstSentence(it.en, cap);
}

function dailyCard(date, items, counts, skips, cap) {
  // five picks with the most visual / brand appeal (see pickCard), each as a title link + one EN line
  const feats = pickCard(items);
  const lines = feats.map((i) => {
    const it = items[i];
    const watch = it.video ? ` [▶ Watch](${it.video})` : "";
    return `**[${md(it.t)}](${it.url})**${watch} <font color="grey">${md(it.tag)} · ${md(it.src)}${reactions(counts, skips, `${date}-${i + 1}`)}</font>\n${blurb(it, cap)}`;
  });
  const els = [
    { tag: "markdown", content: lines.join("\n\n") },
    { tag: "hr" },
    { tag: "markdown", content: `[All ${items.length} stories →](${SITE}/${date.replace(/-/g, "")}.html)` },
  ];
  return {
    schema: "2.0",
    config: { wide_screen_mode: true, update_multi: true },
    header: { title: { tag: "plain_text", content: "ADUX Daily · " + date }, template: "red" },
    body: { elements: els },
  };
}

function weeklyCard(w, index, counts, skips, cap) {
  const els = [];
  const t = w.title || {}, intro = w.intro || {};
  els.push({ tag: "markdown", content: `**${md(t.en || "")}**\n${clip(intro.en, cap * 2)}` });
  els.push({ tag: "hr" });
  els.push({ tag: "markdown", content: (w.cats || []).map((c) => `**${md(c.tag)}** ${clip(c.en, cap)}`).join("\n") });
  const line = (tp, mark) => {
    const it = index[tp.id];
    return it ? `· [${md(it.t)}](${it.url}) ${mark}${tp.n}` : "";
  };
  const top = (w.top || []).map((tp) => line(tp, "❤")).filter(Boolean);
  const sk = ((w.feedback || {}).skipped || []).map((tp) => line(tp, "✕")).filter(Boolean);
  if (top.length || sk.length) {
    els.push({ tag: "hr" });
    let s = "";
    if (top.length) s += "**❤ Most loved**\n" + top.join("\n") + "\n";
    if (sk.length) s += "**✕ Not for us**\n" + sk.join("\n");
    els.push({ tag: "markdown", content: s.trim() });
  }
  const acts = ((w.feedback || {}).actions) || {};
  if (acts.en) {
    els.push({ tag: "hr" });
    els.push({ tag: "markdown", content: `**↻ Next week** ${clip(acts.en, cap * 2)}` });
  }
  els.push({ tag: "hr" });
  els.push({ tag: "markdown", content: `[Full weekly →](${SITE}/weekly.html#${w.week})` });
  return {
    schema: "2.0",
    config: { wide_screen_mode: true, update_multi: true },
    header: { title: { tag: "plain_text", content: `ADUX Weekly · ${w.week}  (${w.from} – ${w.to})` }, template: "red" },
    body: { elements: els },
  };
}

function fitCard(build) {
  for (const cap of [120, 100, 85, 70]) {
    const card = build(cap);
    if (new TextEncoder().encode(JSON.stringify(card)).length <= CARD_LIMIT) return card;
  }
  return build(80);
}

async function feishuSign(secret, ts) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(ts + "\n" + secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new Uint8Array(0));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));
}

async function feishuSend(env, card) {
  if (!env.FEISHU_WEBHOOK) throw new Error("FEISHU_WEBHOOK not set");
  const body = { msg_type: "interactive", card };
  if (env.FEISHU_SECRET) {
    const ts = String(Math.floor(Date.now() / 1000));
    body.timestamp = ts;
    body.sign = await feishuSign(env.FEISHU_SECRET, ts);
  }
  const r = await fetch(env.FEISHU_WEBHOOK, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const txt = await r.text();
  let j = {};
  try { j = JSON.parse(txt); } catch {}
  const ok = r.ok && ((j.code === 0) || (j.StatusCode === 0));
  if (!ok) throw new Error("feishu " + r.status + " " + txt.slice(0, 200));
  return j;
}

async function liveCounts(env) {
  const [counts, skips] = await Promise.all([listCounts(env, "c:", 1000), listCounts(env, "s:", 1000)]);
  return { counts, skips };
}

async function buildDaily(env, date) {
  const items = await siteJson("data/" + date + ".json");
  if (!items) return null;
  const { counts, skips } = await liveCounts(env);
  return fitCard((cap) => dailyCard(date, items, counts, skips, cap));
}

async function buildWeekly(env, week) {
  const w = await siteJson("weekly/" + week + ".json");
  if (!w) return null;
  const all = (await siteJson("items.json")) || [];
  const index = {};
  for (const it of all) index[it.id] = it;
  const { counts, skips } = await liveCounts(env);
  return fitCard((cap) => weeklyCard(w, index, counts, skips, cap));
}

async function runCron(env) {
  const today = beijingDate();
  const log = [];
  if (!(await env.LIKES.get("sent:" + today))) {
    const card = await buildDaily(env, today);
    if (card) {
      await feishuSend(env, card);
      await env.LIKES.put("sent:" + today, new Date().toISOString(), { expirationTtl: 60 * 86400 });
      log.push("daily " + today + " sent");
    } else log.push("daily " + today + " not published yet");
  } else log.push("daily " + today + " already sent");
  if (beijingWeekday() === 1) {
    const week = prevWeekId(today);
    if (!(await env.LIKES.get("sentw:" + week))) {
      const card = await buildWeekly(env, week);
      if (card) {
        await feishuSend(env, card);
        await env.LIKES.put("sentw:" + week, new Date().toISOString(), { expirationTtl: 60 * 86400 });
        log.push("weekly " + week + " sent");
      } else log.push("weekly " + week + " not published yet");
    } else log.push("weekly " + week + " already sent");
  }
  return log;
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runCron(env).then((l) => console.log(l.join("; "))).catch((e) => console.error("cron: " + e.message)));
  },

  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req) });

    if (req.method === "GET" && url.pathname === "/") return json(req, { ok: true, v: 3, feishu: !!env.FEISHU_WEBHOOK });

    if (req.method === "GET" && url.pathname === "/feishu/preview") {
      try {
        const week = url.searchParams.get("week");
        const card = week ? await buildWeekly(env, week) : await buildDaily(env, url.searchParams.get("date") || beijingDate());
        if (!card) return json(req, { error: "not published" }, 404);
        return json(req, { bytes: new TextEncoder().encode(JSON.stringify(card)).length, card });
      } catch (e) { return json(req, { error: e.message }, 500); }
    }

    if (req.method === "GET" && url.pathname === "/feishu/status") {
      const today = beijingDate();
      return json(req, { today, sent: await env.LIKES.get("sent:" + today), weekly: beijingWeekday() === 1 ? await env.LIKES.get("sentw:" + prevWeekId(today)) : null, webhook: !!env.FEISHU_WEBHOOK });
    }

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
