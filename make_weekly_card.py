#!/usr/bin/env python3
"""Build the Monday WeCom card from weekly/<week>.json.
  python3 make_weekly_card.py 2026-W36
Trilingual intro + one line per category (EN, then 中/한 clipped) + most-loved list.
Stays under WeCom's 4096-byte markdown limit by shrinking caps.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://hmi.supermatrix.app"
LIMIT = 4096
ENDS = "。．.!?！？…"


def clip(s, max_bytes):
    if len(s.encode()) <= max_bytes:
        return s
    out = s
    while len(out.encode()) > max_bytes and out:
        out = out[:-1]
    best = max(out.rfind(ch) for ch in ENDS)
    if best >= int(len(out) * 0.45):
        return out[:best + 1]
    return out.rstrip(" ,、，—-") + "…"


def load_index():
    idx = {}
    import glob
    for f in glob.glob(os.path.join(HERE, "data", "*.json")):
        d = os.path.basename(f)[:-5]
        for i, it in enumerate(json.load(open(f)), 1):
            idx["%s-%d" % (d, i)] = it
    return idx


def assemble(w, idx, counts, cap_intro, cap_cat, n_top):
    head = "# ADUX Weekly · %s\n**%s – %s**\n" % (w["week"], w["from"], w["to"])
    t = w.get("title", {})
    body = head + "**%s**\n" % t.get("en", "")
    intro = w.get("intro", {})
    body += "> **EN** %s\n> **中** %s\n> **한** %s\n" % (
        clip(intro.get("en", ""), cap_intro), clip(intro.get("zh", ""), cap_intro), clip(intro.get("ko", ""), cap_intro))
    body += "\n━━━━━━━\n"
    for c in w.get("cats", []):
        body += "**%s** %s\n" % (c["tag"], clip(c.get("en", ""), cap_cat))
        if cap_cat >= 120:
            body += "> 中 %s\n> 한 %s\n" % (clip(c.get("zh", ""), cap_cat), clip(c.get("ko", ""), cap_cat))
    # most loved
    top = w.get("top") or []
    if not top:
        ids = [k for k in idx if w["from"] <= k[:10] <= w["to"]]
        ranked = sorted(((counts.get(i, 0), i) for i in ids), reverse=True)
        top = [{"id": i, "n": n} for n, i in ranked if n > 0]
    if top and n_top:
        body += "\n━━━━━━━\n**❤ Most loved**\n"
        for tp in top[:n_top]:
            it = idx.get(tp["id"] if isinstance(tp, dict) else tp)
            if not it:
                continue
            n = tp.get("n", 0) if isinstance(tp, dict) else counts.get(tp, 0)
            body += "· [%s](%s)%s\n" % (it["t"], it["url"], (" ❤%d" % n) if n else "")
    body += "\n━━━━━━━\n[📑 Full weekly · %s](%s/weekly.html#%s)" % (
        SITE.replace("https://", ""), SITE, w["week"])
    return body


def build(w, idx, counts):
    for cap_intro, cap_cat, n_top in ((400, 300, 5), (320, 240, 5), (260, 200, 5), (220, 170, 3),
                                      (180, 140, 3), (150, 120, 3), (130, 100, 3), (110, 90, 0), (90, 70, 0)):
        c = assemble(w, idx, counts, cap_intro, cap_cat, n_top)
        if len(c.encode()) <= LIMIT:
            return c, (cap_intro, cap_cat)
    return c, (90, 70)


if __name__ == "__main__":
    week = sys.argv[1]
    w = json.load(open(os.path.join(HERE, "weekly", week + ".json")))
    try:
        counts = json.load(open(os.path.join(HERE, "likes.json"))).get("counts", {})
    except Exception:
        counts = {}
    c, cap = build(w, load_index(), counts)
    n = len(c.encode())
    print("weekly card bytes: %d / %d (caps %s)" % (n, LIMIT, cap))
    if n > LIMIT:
        sys.exit("weekly card too large")
    os.makedirs(os.path.join(HERE, "outbox"), exist_ok=True)
    json.dump({"msgtype": "markdown", "markdown": {"content": c}},
              open(os.path.join(HERE, "outbox", "card.json"), "w"), ensure_ascii=False)
    print("wrote outbox/card.json")
