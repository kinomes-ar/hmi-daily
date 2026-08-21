#!/usr/bin/env python3
"""Build the WeCom markdown card for one date -> outbox/card.json"""
import json, os, sys

SITE = "https://hmi.supermatrix.app"
SEP = "\n━━━━━━━━━━━━━\n\n"
LIMIT = 4096
HERE = os.path.dirname(os.path.abspath(__file__))

def build(items, date):
    parts = ["# HMI Daily · %s\n" % date]
    for i, it in enumerate(items, 1):
        n = "①②③④⑤⑥⑦⑧⑨"[i-1] if i <= 9 else str(i)
        parts.append(
            "**{n} {t}**\n> **EN** {en}\n> **中文** {zh}\n> **한국어** {ko}\n\n"
            "[▸ {src}]({url})\n".format(n=n, t=it["t"], en=it["en"], zh=it["zh"],
                                        ko=it["ko"], src=it["src"], url=it["url"])
        )
    c = parts[0] + SEP.join(parts[1:])
    c += "\n━━━━━━━━━━━━━\n[📑 Full archive · %s](%s)" % (SITE.replace("https://", ""), SITE)
    return c

if __name__ == "__main__":
    date = sys.argv[1]
    items = json.load(open(os.path.join(HERE, "data", date + ".json")))
    c = build(items, date)
    n = len(c.encode())
    print("card bytes: %d / %d" % (n, LIMIT))
    if n > LIMIT:
        sys.exit("card too large")
    json.dump({"msgtype": "markdown", "markdown": {"content": c}},
              open(os.path.join(HERE, "outbox", "card.json"), "w"), ensure_ascii=False)
    print("wrote outbox/card.json")
