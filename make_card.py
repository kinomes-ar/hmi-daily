#!/usr/bin/env python3
"""Build the WeCom markdown card for one date -> outbox/card.json

WeCom caps a markdown message at 4096 bytes, so a 12-story edition cannot carry
full trilingual summaries for everything. The card gives the top stories the full
treatment, lists the remainder as headline links, and points at the archive.
"""
import json, os, sys

SITE = "https://hmi.supermatrix.app"
SEP = "\n━━━━━━━━━━━━━\n\n"
LIMIT = 4096
HERE = os.path.dirname(os.path.abspath(__file__))
NUM = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"


def num(i):
    return NUM[i - 1] if i <= len(NUM) else str(i)


def full(i, it):
    return ("**{n} {t}**\n> **EN** {en}\n> **中文** {zh}\n> **한국어** {ko}\n\n"
            "[▸ {src}]({url})\n").format(n=num(i), t=it["t"], en=it["en"],
                                         zh=it["zh"], ko=it["ko"],
                                         src=it["src"], url=it["url"])


def brief(i, it):
    return "{n} [{t}]({url}) · {src}".format(n=num(i), t=it["t"], url=it["url"], src=it["src"])


def assemble(items, date, n_full):
    head = "# HMI Daily · %s\n" % date
    blocks = [full(i, it) for i, it in enumerate(items[:n_full], 1)]
    body = head + SEP.join(blocks)
    rest = items[n_full:]
    if rest:
        lines = [brief(i, it) for i, it in enumerate(rest, n_full + 1)]
        body += "\n━━━━━━━━━━━━━\n**MORE**\n" + "\n".join(lines) + "\n"
    body += "\n━━━━━━━━━━━━━\n[📑 Full archive · %s](%s)" % (SITE.replace("https://", ""), SITE)
    return body


def build(items, date):
    """Give as many stories the full treatment as the byte budget allows."""
    best = assemble(items, date, 1)
    for n in range(2, len(items) + 1):
        cand = assemble(items, date, n)
        if len(cand.encode()) > LIMIT:
            break
        best = cand
    return best


if __name__ == "__main__":
    date = sys.argv[1]
    items = json.load(open(os.path.join(HERE, "data", date + ".json")))
    c = build(items, date)
    n = len(c.encode())
    print("card bytes: %d / %d  (%d stories)" % (n, LIMIT, len(items)))
    if n > LIMIT:
        sys.exit("card too large")
    json.dump({"msgtype": "markdown", "markdown": {"content": c}},
              open(os.path.join(HERE, "outbox", "card.json"), "w"), ensure_ascii=False)
    print("wrote outbox/card.json")
