#!/usr/bin/env python3
"""Build the WeCom markdown card for one date -> outbox/card.json

Guarantees FIVE featured stories with trilingual summaries:
the lead, plus the first story from each coverage group —
HMI (Cockpit/Interaction), AI, and design (Design/Visual/Industrial) —
topped up with the next-ranked stories. If the 4096-byte WeCom cap is
tight, per-language summaries are clipped at sentence boundaries rather
than dropping a featured slot. Everything else lists as linked headlines.
"""
import json, os, sys

SITE = "https://hmi.supermatrix.app"
SEP = "\n━━━━━━━\n\n"
LIMIT = 4096
N_FEATURED = 5
HERE = os.path.dirname(os.path.abspath(__file__))
NUM = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
GROUPS = [("cockpit", "interaction"), ("ai",), ("design", "visual", "industrial")]
ENDS = "。．.!?！？…"


def num(i):
    return NUM[i - 1] if i <= len(NUM) else str(i)


def pick_featured(items):
    feats = [0] if items else []
    for g in GROUPS:
        for i, it in enumerate(items):
            if i in feats:
                continue
            if (it.get("tag", "") or "").strip().lower() in g:
                feats.append(i)
                break
        if len(feats) >= N_FEATURED:
            break
    i = 0
    while len(feats) < min(N_FEATURED, len(items)):
        if i not in feats:
            feats.append(i)
        i += 1
    return sorted(feats)


def clip(s, max_bytes):
    if len(s.encode()) <= max_bytes:
        return s
    out = s
    while len(out.encode()) > max_bytes and out:
        out = out[:-1]
    # prefer ending on a sentence
    best = -1
    for ch in ENDS:
        p = out.rfind(ch)
        if p > best:
            best = p
    if best >= int(len(out) * 0.45):
        return out[:best + 1]
    return out.rstrip(" ,、，—-") + "…"


def full(i, it, cap):
    return ("**{n} [{t}]({url})**\n> **EN** {en}\n> **中** {zh}\n> **한** {ko}\n").format(
        n=num(i), t=it["t"], en=clip(it["en"], cap), zh=clip(it["zh"], cap),
        ko=clip(it["ko"], cap), url=it["url"])


def brief(i, it):
    return "{n} [{t}]({url})".format(n=num(i), t=it["t"], url=it["url"])


def assemble(items, date, cap):
    feats = pick_featured(items)
    head = "# ADUX Daily · %s\n" % date
    blocks = [full(i + 1, items[i], cap) for i in feats]
    body = head + SEP.join(blocks)
    rest = [(i + 1, it) for i, it in enumerate(items) if i not in feats]
    if rest:
        body += "\n━━━━━━━\n**MORE**\n" + "\n".join(brief(i, it) for i, it in rest) + "\n"
    body += "\n━━━━━━━\n[📑 Full archive · %s](%s)" % (SITE.replace("https://", ""), SITE)
    return body


def build(items, date):
    for cap in (10_000, 300, 240, 200, 170, 145, 120, 100, 85, 70):
        c = assemble(items, date, cap)
        if len(c.encode()) <= LIMIT:
            return c, cap
    return c, 85


if __name__ == "__main__":
    date = sys.argv[1]
    items = json.load(open(os.path.join(HERE, "data", date + ".json")))
    c, cap = build(items, date)
    n = len(c.encode())
    print("card bytes: %d / %d  (%d stories, %d featured, cap %s)" %
          (n, LIMIT, len(items), min(N_FEATURED, len(items)), cap))
    if n > LIMIT:
        sys.exit("card too large even at minimum cap")
    json.dump({"msgtype": "markdown", "markdown": {"content": c}},
              open(os.path.join(HERE, "outbox", "card.json"), "w"), ensure_ascii=False)
    print("wrote outbox/card.json")
