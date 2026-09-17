#!/usr/bin/env python3
"""Validate a daily edition before publishing.

  python3 check_edition.py data/2026-09-15.json   # schema, tags, lengths, domains, dedupe, card size
  python3 check_edition.py --recent               # print URLs/titles of the last 15 editions (for dedupe)

Exit code 1 on any ERROR; WARNs are printed but do not fail.
"""
import glob, json, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TAGS = {"Cockpit", "Interaction", "AI", "Design", "Visual", "Industrial", "Micromobility", "Motion"}
HMI = {"Cockpit", "Interaction"}
BLOCK = ("guideautoweb", "msn.com", "yahoo.com", "news.google", "newsbreak", "flipboard",
         "medium.com", "linkedin.com", "facebook.com", "x.com", "twitter.com", "reddit.com",
         "freeyork.org", "archyde", "pressreader", "apple.news", "bing.com")
PIN_IMG = ("carscoops.com", "motorcycle.com", "wardsauto.com")
LIMITS = {"t": (20, 60), "en": (200, 640), "zh": (60, 320), "ko": (80, 400)}


def recent(exclude=None, n=15):
    files = sorted(glob.glob(os.path.join(DATA, "*.json")))
    if exclude:
        files = [f for f in files if os.path.abspath(f) != os.path.abspath(exclude)]
    out = []
    for f in files[-n:]:
        d = os.path.basename(f)[:-5]
        try:
            for it in json.load(open(f)):
                out.append((d, it.get("url", ""), it.get("t", "")))
        except Exception as e:
            print("WARN cannot read %s: %s" % (f, e))
    return out


def words(s):
    return set(w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3)


def main(path):
    errs, warns = [], []
    try:
        items = json.load(open(path))
    except Exception as e:
        print("ERROR invalid JSON: %s" % e); return 1
    if not isinstance(items, list):
        print("ERROR top level must be a JSON array"); return 1
    n = len(items)
    if n < 12:
        errs.append("only %d stories (need 16)" % n)
    elif n != 16:
        warns.append("%d stories (target 16)" % n)

    past = recent(exclude=path)
    past_urls = {u.rstrip("/") for _, u, _ in past}
    past_titles = [(d, t, words(t)) for d, t, _ in [(d, t, u) for d, u, t in past]]
    seen = set()
    tags = []
    for i, it in enumerate(items, 1):
        p = "#%d" % i
        if not isinstance(it, dict):
            errs.append("%s not an object" % p); continue
        for k in ("tag", "t", "en", "zh", "ko", "src", "url"):
            if not it.get(k) or not isinstance(it[k], str):
                errs.append("%s missing field %s" % (p, k))
        if errs and errs[-1].startswith(p):
            continue
        if it["tag"] not in TAGS:
            errs.append("%s bad tag %r" % (p, it["tag"]))
        tags.append(it["tag"])
        b = it.get("blurb", "")
        if not b:
            warns.append("%s missing blurb (one-line EN takeaway for the chat card)" % p)
        elif not (50 <= len(b) <= 100):
            warns.append("%s blurb length %d (want 60-95)" % (p, len(b)))
        for k, (lo, hi) in LIMITS.items():
            L = len(it[k])
            if L < lo:
                warns.append("%s %s too short (%d < %d)" % (p, k, L, lo))
            if L > hi:
                warns.append("%s %s too long (%d > %d)" % (p, k, L, hi))
        u = it["url"].strip()
        host = urllib.parse.urlparse(u).netloc.lower()
        if not u.startswith("https://") or not host:
            errs.append("%s url must be https: %s" % (p, u))
        if any(b in host for b in BLOCK):
            errs.append("%s url on a blocked/aggregator domain: %s" % (p, host))
        if u.rstrip("/") in seen:
            errs.append("%s duplicate url within edition" % p)
        seen.add(u.rstrip("/"))
        if u.rstrip("/") in past_urls:
            errs.append("%s url already published in a previous edition: %s" % (p, u))
        if it["tag"] == "Motion" and not it.get("video"):
            errs.append("%s Motion story needs a video link" % p)
        if it.get("video") and not str(it["video"]).startswith("https://"):
            errs.append("%s video must be an https URL" % p)
        if any(k in host for k in PIN_IMG) and not it.get("img_url"):
            errs.append("%s %s needs a pinned img_url (bot-walled site)" % (p, host))
        if it.get("img") or it.get("img_src"):
            warns.append("%s has img/img_src — leave those to the GitHub Action" % p)
        w = words(it["t"])
        for d, t, pw in past_titles:
            if len(w) >= 3 and len(w & pw) >= max(3, int(0.6 * len(w))):
                warns.append("%s title resembles %s %r — same story?" % (p, d, t))
        for k in ("en", "zh", "ko"):
            if "\n" in it[k]:
                warns.append("%s %s contains a newline" % (p, k))
        if re.search(r"[一-鿿]", it["en"]) or re.search(r"[가-힣]", it["en"]):
            errs.append("%s en contains CJK text" % p)
        if not re.search(r"[一-鿿]", it["zh"]):
            errs.append("%s zh is not Chinese" % p)
        if not re.search(r"[가-힣]", it["ko"]):
            errs.append("%s ko is not Korean" % p)

    picks = sum(1 for it in items if isinstance(it, dict) and it.get("pick") is True)
    if picks != 5:
        warns.append("%d stories have \"pick\": true (the chat card wants exactly 5)" % picks)
    hmi = sum(1 for t in tags if t in HMI)
    vis = sum(1 for t in tags if t == "Visual")
    if hmi < 2:
        warns.append("only %d Cockpit/Interaction stories (want 3-4)" % hmi)
    if vis < 3:
        warns.append("only %d Visual stories (want 4-5)" % vis)
    if tags and tags[0] not in HMI:
        warns.append("lead story is %s — prefer a Cockpit/Interaction lead when one exists" % tags[0])
    # quotas set by the team's reactions (feedback.py); ±1 per group is tolerated
    try:
        sys.path.insert(0, HERE)
        import feedback
        hearts, skips, _ = feedback.load_snapshot()
        date = os.path.basename(path)[:-5]
        rows = feedback.stories(feedback.editions(before=date)[-feedback.WINDOW:], hearts, skips)
        q, _notes = feedback.quotas(rows)
        have = {g: 0 for g in q}
        for t in tags:
            have[feedback.group_of(t)] += 1
        for g in q:
            if abs(have[g] - q[g]) > 1:
                warns.append("quota: %s has %d stories, feedback.py asked for %d (run: python3 feedback.py --brief)" % (g, have[g], q[g]))
    except Exception as e:
        warns.append("could not check quotas: %s" % e)

    if not errs:
        try:
            sys.path.insert(0, HERE)
            import make_card
            date = os.path.basename(path)[:-5]
            c, cap = make_card.build(items, date)
            b = len(c.encode())
            print("card: %d / 4096 bytes (cap %s)" % (b, cap))
            if b > 4096:
                errs.append("card too large even at minimum cap — shorten summaries")
        except Exception as e:
            warns.append("could not size the card: %s" % e)

    for w in warns:
        print("WARN  " + w)
    for e in errs:
        print("ERROR " + e)
    print("%s: %d stories, tags %s" % (os.path.basename(path), n,
          {t: tags.count(t) for t in sorted(set(tags))}))
    print("RESULT: %s" % ("FAIL" if errs else "OK"))
    return 1 if errs else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--recent":
        for d, u, t in recent():
            print("%s | %s | %s" % (d, t, u))
        sys.exit(0)
    sys.exit(main(sys.argv[1]))
