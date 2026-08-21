#!/usr/bin/env python3
"""Pull each story's lead image from its source article and store it in assets/.
Runs on a GitHub Actions runner (unrestricted network). Idempotent: items that
already carry a local "img" path are skipped. Failures are non-fatal — the page
falls back to a typographic panel.
"""
import json, glob, os, re, sys, mimetypes
import urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ASSETS = os.path.join(HERE, "assets")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MAX_BYTES = 8 * 1024 * 1024

META = re.compile(
    rb'<meta[^>]+?(?:property|name)\s*=\s*["\'](og:image(?::secure_url|:url)?|twitter:image(?::src)?)["\'][^>]*>',
    re.I)
CONTENT = re.compile(rb'content\s*=\s*["\']([^"\']+)["\']', re.I)
EXT = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png",
       "image/webp": ".webp", "image/gif": ".gif", "image/avif": ".avif"}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return urllib.request.urlopen(req, timeout=timeout)


IMG_TAG = re.compile(rb'<img\b[^>]*>', re.I)
SRC = re.compile(rb'\b(?:data-src|data-original|src)\s*=\s*["\']([^"\']+)["\']', re.I)
SRCSET = re.compile(rb'\bsrcset\s*=\s*["\']([^"\']+)["\']', re.I)
JUNK = ("logo", "icon", "sprite", "avatar", "placeholder", "blank", "pixel",
        "spacer", "1x1", "badge", "favicon", "share", "banner-ad", "/ads/")


def _clean(raw, base):
    raw = raw.decode("utf-8", "ignore").strip().replace("&amp;", "&")
    if not raw or raw.startswith("data:"):
        return None
    return urllib.parse.urljoin(base, raw)


def image_candidates(page_url):
    """og:image / twitter:image first, then the article's own <img> tags."""
    with get(page_url) as r:
        body = r.read(900_000)
        base = r.geturl()
    out = []
    for m in META.finditer(body):
        c = CONTENT.search(m.group(0))
        if c:
            u = _clean(c.group(1), base)
            if u:
                out.append(u)
    for m in IMG_TAG.finditer(body):
        tag = m.group(0)
        ss = SRCSET.search(tag)
        if ss:
            # take the widest entry of the srcset
            parts = [p.strip().split()[0] for p in ss.group(1).split(b",") if p.strip()]
            if parts:
                u = _clean(parts[-1], base)
                if u:
                    out.append(u)
        sm = SRC.search(tag)
        if sm:
            u = _clean(sm.group(1), base)
            if u:
                out.append(u)
    seen, keep = set(), []
    for u in out:
        low = u.lower()
        if u in seen or low.endswith(".svg") or any(j in low for j in JUNK):
            continue
        seen.add(u)
        keep.append(u)
    return keep[:12]


def download(img_url, stem):
    with get(img_url) as r:
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        blob = r.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES or len(blob) < 25_000:
        raise ValueError("size %dB out of range" % len(blob))
    ext = EXT.get(ctype) or os.path.splitext(urllib.parse.urlparse(img_url).path)[1].lower()
    if ext not in EXT.values():
        ext = ".jpg"
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, stem + ext)
    with open(path, "wb") as f:
        f.write(blob)
    return "assets/" + stem + ext


def main():
    changed = 0
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        date = os.path.basename(f)[:-5]
        items = json.load(open(f))
        dirty = False
        for i, it in enumerate(items, 1):
            if it.get("img") and os.path.exists(os.path.join(HERE, it["img"])):
                continue
            stem = "%s-%d" % (date, i)
            # "img_from" lets an item keep its primary source link while pulling
            # the picture from a mirror that actually serves one.
            pages = [u for u in (it.get("img_from"), it["url"]) if u]
            cands = []
            for page in pages:
                try:
                    cands = image_candidates(page)
                except Exception as e:
                    print("  page unreachable %s :: %s" % (page[:60], e)); continue
                if cands:
                    break
            if not cands:
                print("  no candidates  %s" % it["url"][:70]); continue
            for img_url in cands:
                try:
                    it["img"] = download(img_url, stem)
                    it["img_src"] = img_url
                    dirty = True; changed += 1
                    print("  saved %s  <- %s" % (it["img"], img_url[:80]))
                    break
                except Exception as e:
                    print("    skip %s :: %s" % (img_url[:60], e))
            else:
                print("  FAILED all %d candidates for %s" % (len(cands), it["url"][:60]))
        if dirty:
            json.dump(items, open(f, "w"), ensure_ascii=False, indent=1)
            print("updated %s" % f)
    print("done, %d image(s) added" % changed)


if __name__ == "__main__":
    main()
