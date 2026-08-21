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


def find_image_url(page_url):
    with get(page_url) as r:
        head = r.read(400_000)          # meta tags live near the top
        base = r.geturl()
    for m in META.finditer(head):
        c = CONTENT.search(m.group(0))
        if not c:
            continue
        raw = c.group(1).decode("utf-8", "ignore").strip()
        raw = raw.replace("&amp;", "&")
        if not raw or raw.startswith("data:"):
            continue
        return urllib.parse.urljoin(base, raw)
    return None


def download(img_url, stem):
    with get(img_url) as r:
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        blob = r.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES or len(blob) < 1000:
        raise ValueError("size %d out of range" % len(blob))
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
            try:
                img_url = find_image_url(it["url"])
                if not img_url:
                    print("  no og:image  %s" % it["url"]); continue
                it["img"] = download(img_url, stem)
                it["img_src"] = img_url
                dirty = True; changed += 1
                print("  saved %s  <- %s" % (it["img"], img_url[:80]))
            except Exception as e:
                print("  FAILED %s :: %s" % (it["url"][:70], e))
        if dirty:
            json.dump(items, open(f, "w"), ensure_ascii=False, indent=1)
            print("updated %s" % f)
    print("done, %d image(s) added" % changed)


if __name__ == "__main__":
    main()
