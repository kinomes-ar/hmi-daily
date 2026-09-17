#!/usr/bin/env python3
"""Turn the team's reactions (hearts / "not for me") into concrete editorial guidance.

  python3 feedback.py --brief              guidance for TODAY's edition (last 3 weeks of reactions)
  python3 feedback.py --week 2026-W37      stats + suggested actions for that week's summary (JSON)
  python3 feedback.py --fetch --brief      refresh likes.json from the Worker first (needs network)

Rules are deterministic and printed with the result so the weekly summary can explain them.

  Groups (16 stories):  HMI = Cockpit+Interaction, Micromobility, AI, Visual = Visual+Motion, Product = Design+Industrial
  Base quotas:          HMI 4 · Micromobility 2 · AI 2 · Visual 4 · Product 4
  Signal window:        the 15 most recent editions before today (~3 weeks)
  Score per group:      net = hearts - skips ; rate = net / stories
  Quota moves:          need >= 5 reactions in the window, else base quotas.
                        best-rate group (rate > 0)  -> +1 ; worst-rate group (rate < 0) -> -1
                        with >= 20 reactions the best group may take +2
                        if no group is negative, the +1 is paid by Product/Visual (lowest rate first)
                        floors: HMI >= 3, Visual >= 3, others >= 1 ; cap: base + 2 ; total always 16
  Sources:              >= 3 stories in window: skips >= 2 and skips > hearts -> "deprioritise"
                        hearts >= 2 and hearts > skips -> "favour"
  Topics:               hearted / skipped titles are listed so the editor can read the themes.
"""
import glob, json, os, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
GROUPS = [("HMI", ("Cockpit", "Interaction")), ("Micromobility", ("Micromobility",)), ("AI", ("AI",)),
          ("Visual", ("Visual", "Motion")), ("Product", ("Design", "Industrial"))]
BASE = {"HMI": 4, "Micromobility": 2, "AI": 2, "Visual": 4, "Product": 4}
FLOOR = {"HMI": 3, "Micromobility": 1, "AI": 1, "Visual": 3, "Product": 1}
WINDOW = 15


def group_of(tag):
    for g, tags in GROUPS:
        if tag in tags:
            return g
    return "Product"


def load_snapshot():
    try:
        j = json.load(open(os.path.join(HERE, "likes.json")))
        return j.get("counts", {}), j.get("skips", {}), j.get("updated", "")
    except Exception:
        return {}, {}, ""


def fetch_snapshot():
    api = json.load(open(os.path.join(HERE, "site.json"))).get("like_api", "").rstrip("/")
    import urllib.request
    req = urllib.request.Request(api + "/top?n=1000", headers={
        "User-Agent": "Mozilla/5.0 (ADUX Daily feedback)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    json.dump({"updated": dt.date.today().isoformat(), "counts": data.get("counts", {}),
               "skips": data.get("skips", {})}, open(os.path.join(HERE, "likes.json"), "w"), indent=0)
    print("fetched: %d hearted, %d skipped ids" % (len(data.get("counts", {})), len(data.get("skips", {}))))


def editions(before=None, after=None):
    out = []
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        d = os.path.basename(f)[:-5]
        if before and d >= before:
            continue
        if after and d < after:
            continue
        try:
            out.append((d, json.load(open(f))))
        except Exception:
            pass
    return out


def stories(eds, hearts, skips):
    rows = []
    for d, items in eds:
        for i, it in enumerate(items, 1):
            iid = "%s-%d" % (d, i)
            rows.append({"id": iid, "date": d, "tag": it.get("tag", ""), "group": group_of(it.get("tag", "")),
                         "src": it.get("src", ""), "t": it.get("t", ""), "url": it.get("url", ""),
                         "l": hearts.get(iid, 0), "s": skips.get(iid, 0)})
    return rows


def bucket(rows, key):
    b = {}
    for r in rows:
        x = b.setdefault(r[key], {"n": 0, "l": 0, "s": 0})
        x["n"] += 1; x["l"] += r["l"]; x["s"] += r["s"]
    for x in b.values():
        x["net"] = x["l"] - x["s"]
        x["rate"] = round(x["net"] / x["n"], 3) if x["n"] else 0.0
    return b


def quotas(rows):
    """Return (quotas dict, list of explanation lines)."""
    q = dict(BASE)
    g = bucket(rows, "group")
    total = sum(x["l"] + x["s"] for x in g.values())
    notes = []
    if total < 5:
        notes.append("%d reaction(s) in the window (< 5): not enough signal, base quotas apply." % total)
        return q, notes
    ranked = sorted(g.items(), key=lambda kv: (kv[1]["rate"], kv[1]["net"]), reverse=True)
    best, worst = ranked[0], ranked[-1]
    moves = 0
    if best[1]["rate"] > 0 and q[best[0]] < BASE[best[0]] + 2:
        q[best[0]] += 1; moves += 1
        notes.append("%s +1 (best net rate %+.2f per story: %d hearts, %d skips)." % (
            best[0], best[1]["rate"], best[1]["l"], best[1]["s"]))
        if total >= 20 and len(ranked) > 2 and ranked[1][1]["rate"] > 0 and q[best[0]] < BASE[best[0]] + 2:
            q[best[0]] += 1; moves += 1
            notes.append("%s +1 more (>= 20 reactions and still the clear favourite)." % best[0])
    givers = []
    if worst[1]["rate"] < 0 and q[worst[0]] > FLOOR[worst[0]]:
        givers.append(worst)
        notes.append("%s -1 (worst net rate %+.2f: %d hearts, %d skips)." % (
            worst[0], worst[1]["rate"], worst[1]["l"], worst[1]["s"]))
    # keep the total at 16: every + must be paid for by a -
    taken = 0
    for name, x in givers:
        if taken < moves:
            q[name] -= 1; taken += 1
    if taken < moves:
        # nobody is negative: pay from the big discretionary groups (Product, Visual), lowest rate first —
        # never from the core beats (HMI, Micromobility, AI) unless the team actually skipped them
        pool = sorted([(n, x) for n, x in ranked if n in ("Product", "Visual") and n != best[0]],
                      key=lambda kv: kv[1]["rate"])
        for name, x in pool:
            while taken < moves and q[name] > FLOOR[name]:
                q[name] -= 1; taken += 1
                notes.append("%s -1 (no group is negative; taken from the largest discretionary group to keep 16)." % name)
    if taken < moves:  # nobody can give: undo
        q = dict(BASE); notes.append("floors reached: base quotas apply.")
    assert sum(q.values()) == 16, q
    return q, notes


def source_notes(rows):
    s = bucket(rows, "src")
    fav, dep = [], []
    for name, x in sorted(s.items(), key=lambda kv: -kv[1]["n"]):
        if x["n"] < 3:
            continue
        if x["s"] >= 2 and x["s"] > x["l"]:
            dep.append("%s (%d stories, %d skips, %d hearts)" % (name, x["n"], x["s"], x["l"]))
        elif x["l"] >= 2 and x["l"] > x["s"]:
            fav.append("%s (%d stories, %d hearts, %d skips)" % (name, x["n"], x["l"], x["s"]))
    return fav, dep


def brief(hearts, skips, updated, today=None):
    today = today or dt.date.today().isoformat()
    eds = editions(before=today)[-WINDOW:]
    rows = stories(eds, hearts, skips)
    q, notes = quotas(rows)
    fav, dep = source_notes(rows)
    g = bucket(rows, "group")
    print("ADUX feedback brief — window %s … %s (%d editions, %d stories), snapshot %s" % (
        eds[0][0] if eds else "-", eds[-1][0] if eds else "-", len(eds), len(rows), updated or "n/a"))
    print("\nQUOTAS for today's 16 stories (follow these; ±1 is fine if the day is thin):")
    for name, _ in GROUPS:
        x = g.get(name, {"n": 0, "l": 0, "s": 0, "rate": 0.0})
        print("  %-13s %d   (base %d · window: %d stories, %d hearts, %d skips, rate %+.2f)" % (
            name, q[name], BASE[name], x["n"], x["l"], x["s"], x["rate"]))
    for n in notes:
        print("  · " + n)
    print("\nSOURCES:")
    print("  favour:       " + ("; ".join(fav) if fav else "none yet"))
    print("  deprioritise: " + ("; ".join(dep) if dep else "none") +
          ("\n  (use a deprioritised source only for a clearly strong story; never more than one per edition)" if dep else ""))
    loved = sorted([r for r in rows if r["l"] > r["s"]], key=lambda r: (-r["l"], r["date"]))[:12]
    hated = sorted([r for r in rows if r["s"] > r["l"]], key=lambda r: (-r["s"], r["date"]))[:12]
    print("\nWHAT THE TEAM HEARTED (find more like these — same kind of subject, depth and angle):")
    for r in loved:
        print("  ♥%d  [%s] %s — %s" % (r["l"], r["tag"], r["t"], r["src"]))
    if not loved:
        print("  (nothing yet)")
    print("\nWHAT THE TEAM SKIPPED (avoid this kind of story unless it is unusually strong):")
    for r in hated:
        print("  ✕%d  [%s] %s — %s" % (r["s"], r["tag"], r["t"], r["src"]))
    if not hated:
        print("  (nothing yet)")
    return q


def week_range(week):
    y, w = week.split("-W")
    mon = dt.date.fromisocalendar(int(y), int(w), 1)
    return mon.isoformat(), (mon + dt.timedelta(days=4)).isoformat()


def week_json(week, hearts, skips, updated):
    frm, to = week_range(week)
    rows = stories(editions(after=frm, before=(dt.date.fromisoformat(to) + dt.timedelta(days=1)).isoformat()), hearts, skips)
    cats = bucket(rows, "tag"); srcs = bucket(rows, "src")
    top = sorted([r for r in rows if r["l"] > 0], key=lambda r: (-r["l"], r["date"]))[:5]
    worst = sorted([r for r in rows if r["s"] > 0], key=lambda r: (-r["s"], r["date"]))[:5]
    # next week's quotas use the standard 3-week window ending this Friday
    nxt_rows = stories(editions(before=(dt.date.fromisoformat(to) + dt.timedelta(days=1)).isoformat())[-WINDOW:], hearts, skips)
    q, notes = quotas(nxt_rows)
    fav, dep = source_notes(nxt_rows)
    out = {
        "week": week, "from": frm, "to": to, "snapshot": updated,
        "stats": {"items": len(rows), "hearts": sum(r["l"] for r in rows), "skips": sum(r["s"] for r in rows),
                  "cats": cats, "srcs": {k: v for k, v in srcs.items() if v["l"] or v["s"]}},
        "top": [{"id": r["id"], "n": r["l"]} for r in top],
        "skipped": [{"id": r["id"], "n": r["s"], "t": r["t"]} for r in worst],
        "next_quotas": q, "quota_notes": notes, "favour": fav, "deprioritise": dep,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--fetch" in a:
        fetch_snapshot()
    hearts, skips, updated = load_snapshot()
    if "--week" in a:
        week_json(a[a.index("--week") + 1], hearts, skips, updated)
    elif "--brief" in a or not a:
        today = a[a.index("--today") + 1] if "--today" in a else None
        brief(hearts, skips, updated, today)
    else:
        sys.exit(__doc__)
