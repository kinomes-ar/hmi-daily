#!/usr/bin/env python3
"""Render every data/YYYY-MM-DD.json into the HMI Daily archive page.
  python3 build.py            -> fragment (Claude Artifact)
  python3 build.py standalone -> full document -> index.html
"""
import json, os, sys, glob, html
from datetime import date as _date

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# fallback panel colours, keyed by category
SWATCH = {
    "display":     ("#E5342A", "#FFFFFF"),
    "ar / hud":    ("#1F45C8", "#FFFFFF"),
    "interaction": ("#F0C020", "#141412"),
    "industry":    ("#12916A", "#FFFFFF"),
    "ai":          ("#7A3BD6", "#FFFFFF"),
}
DEFAULT_SWATCH = ("#141412", "#EFEEE9")

CSS = """
:root{
  --ground:#E4E2DB; --paper:#F9F8F5; --ink:#111110; --muted:#6A6862;
  --rule:#D3D0C7; --hair:#E4E1D9; --red:#E5342A; --onred:#FFFFFF;
  --footer:#151513; --footer-ink:#F2F1ED; --shade:#EDEBE4;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#080807; --paper:#131311; --ink:#EDEBE4; --muted:#918D83;
    --rule:#2E2D29; --hair:#252420; --red:#FF4A3D; --onred:#141412;
    --footer:#080807; --footer-ink:#EDEBE4; --shade:#1E1D1A;
  }
}
:root[data-theme="dark"]{
  --ground:#080807; --paper:#131311; --ink:#EDEBE4; --muted:#918D83;
  --rule:#2E2D29; --hair:#252420; --red:#FF4A3D; --onred:#141412;
  --footer:#080807; --footer-ink:#EDEBE4; --shade:#1E1D1A;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"Archivo",-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased;
}
img{max-width:100%; display:block}
.sheet{max-width:1180px; margin:26px auto; background:var(--paper)}
.shell{max-width:1180px; margin:0 auto; padding:0 34px}
@media (max-width:700px){ .sheet{margin:0} .shell{padding:0 20px} }

.top{
  display:flex; align-items:center; justify-content:space-between; gap:14px;
  padding:15px 0; border-bottom:1px solid var(--ink); flex-wrap:wrap;
  font-size:10px; font-weight:700; letter-spacing:.16em; text-transform:uppercase;
}
@media (max-width:700px){
  .top{justify-content:center; gap:12px; padding:14px 0}
  .top .nav{order:3; width:100%; justify-content:center; overflow-x:auto; gap:14px}
}
.top .wordmark{font-family:"Archivo Black",Impact,sans-serif; font-size:15px; letter-spacing:.02em}
.top .nav{display:flex; gap:18px; color:var(--muted); flex-wrap:wrap}
.top .nav a{color:inherit; text-decoration:none}
.top .nav a:hover{color:var(--red)}
.masthead{padding:22px 0 18px; text-align:center; border-bottom:1px solid var(--ink)}
.masthead h1{
  font-family:"Archivo Black",Impact,sans-serif; margin:0;
  font-size:clamp(32px,6.4vw,64px); line-height:.92; letter-spacing:-.03em;
  text-transform:uppercase; text-wrap:balance;
}
.masthead .kicker{
  margin-top:9px; font-size:9.5px; font-weight:600; letter-spacing:.18em;
  text-transform:uppercase; color:var(--muted);
}
@media (max-width:700px){ .masthead{padding:18px 0 14px} }

/* ---- date band ---- */
.day{padding:22px 0 4px}
.day + .day{border-top:2px solid var(--ink)}
.dayhead{display:flex; align-items:baseline; gap:14px; margin-bottom:16px}
.dayhead h2{
  font-family:"Archivo Black",Impact,sans-serif; margin:0;
  font-size:clamp(17px,2.1vw,22px); letter-spacing:-.01em;
  font-variant-numeric:tabular-nums; text-transform:uppercase;
}
.dayhead .rule{flex:1; height:1px; background:var(--ink)}
.dayhead .meta{
  font-size:9.5px; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
  color:var(--muted); white-space:nowrap;
}

/* ---- newspaper grid: lead | middle | narrow rail ---- */
.band{
  display:grid; grid-template-columns:1.62fr 1fr .78fr; gap:0;
  border-top:1px solid var(--ink);
}
.col{padding:16px 20px; border-left:1px solid var(--hair); min-width:0}
.col:first-child{padding-left:0; border-left:0}
.col:last-child{padding-right:0}
.col.mid,.col.side{display:grid; gap:16px; align-content:start}
.col.mid > article + article,
.col.side > article + article{border-top:1px solid var(--hair); padding-top:16px}
.foot-row{
  display:grid; grid-template-columns:repeat(4,1fr); gap:0;
  border-top:1px solid var(--ink); margin-bottom:4px;
}
.foot-row > article{padding:16px 18px; border-left:1px solid var(--hair); min-width:0}
.foot-row > article:first-child{padding-left:0; border-left:0}
@media (max-width:980px){
  .band{grid-template-columns:1.3fr 1fr}
  .col.side{grid-column:1 / -1; grid-template-columns:1fr 1fr 1fr;
            border-left:0; padding:16px 0 0; border-top:1px solid var(--hair)}
  .col.side > article + article{border-top:0; border-left:1px solid var(--hair);
            padding-top:0; padding-left:18px}
  .foot-row{grid-template-columns:1fr 1fr}
  .foot-row > article:nth-child(3){border-left:0; padding-left:0}
}
@media (max-width:660px){
  .band{grid-template-columns:1fr}
  .col{padding:16px 0; border-left:0; border-top:1px solid var(--hair)}
  .col:first-child{border-top:0; padding-top:0}
  .col.side{grid-template-columns:1fr}
  .col.side > article + article{border-left:0; padding-left:0;
            border-top:1px solid var(--hair); padding-top:16px}
  .foot-row{grid-template-columns:1fr}
  .foot-row > article{padding:16px 0; border-left:0; border-top:1px solid var(--hair)}
  .foot-row > article:first-child{border-top:0}
}

/* ---- photos ---- */
.ph{margin:0 0 10px; overflow:hidden; background:var(--shade)}
.ph img{width:100%; height:100%; object-fit:cover}
.ph-lead{aspect-ratio:16/9}
.ph-mid{aspect-ratio:4/3}
.ph-side{aspect-ratio:1/1}
.ph-foot{aspect-ratio:3/2}
.ph.fb{display:flex; align-items:flex-end; padding:10px}
.ph.fb span{
  font-family:"Archivo Black",Impact,sans-serif; text-transform:uppercase;
  line-height:.86; letter-spacing:-.02em; word-break:break-word;
}
.ph-lead.fb span{font-size:clamp(26px,3.6vw,44px)}
.ph-mid.fb span{font-size:21px}
.ph-side.fb span{font-size:15px}
.ph-foot.fb span{font-size:19px}

/* ---- pills ---- */
.tag{
  display:inline-flex; align-items:center; gap:5px;
  background:var(--red); color:var(--onred);
  font-size:8.5px; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
  padding:3px 9px 3px 6px; border-radius:999px; margin-bottom:7px;
}
.tag::before{content:""; width:6px; height:6px; border-radius:50%; background:var(--onred); opacity:.9}
.a-side .tag,.a-foot .tag{
  background:transparent; color:var(--red); border:1px solid var(--red); padding:2px 8px 2px 6px;
}
.a-side .tag::before,.a-foot .tag::before{background:var(--red); opacity:1}

/* ---- headlines & text ---- */
.hl{
  font-family:"Newsreader","Iowan Old Style",Georgia,"Songti SC","Apple SD Gothic Neo",serif;
  font-weight:600; margin:0 0 8px;
  line-height:1.14; letter-spacing:-.01em; text-wrap:balance;
}
.a-lead .hl{font-size:clamp(23px,2.7vw,31px); line-height:1.08; margin-bottom:9px}
.a-mid .hl{font-size:17px}
.a-side .hl{font-size:13.5px; line-height:1.22}
.a-foot .hl{font-size:16px}
.tx{display:none; margin:0; max-width:60ch; color:var(--ink)}
.tx.en{display:block}
html[data-lang="zh"] .tx.en,html[data-lang="ko"] .tx.en{display:none}
html[data-lang="zh"] .tx.zh{display:block}
html[data-lang="ko"] .tx.ko{display:block}
.a-lead .tx{font-size:13.5px; line-height:1.6}
.a-mid .tx{font-size:12.5px; line-height:1.55; color:var(--muted)}
.a-foot .tx{font-size:12.5px; line-height:1.55; color:var(--muted)}
.a-side .tx{display:none !important}
@media (max-width:660px){
  .a-side .hl,.a-foot .hl,.a-mid .hl{font-size:19px}
  .a-lead .hl{font-size:24px}
  .a-mid .tx,.a-foot .tx{font-size:13.5px}
  .ph-side{aspect-ratio:16/9}
}

.langsw{display:flex; gap:0; border:1px solid var(--ink); border-radius:999px; overflow:hidden}
.langsw button{
  appearance:none; border:0; background:transparent; color:var(--ink); cursor:pointer;
  font:inherit; font-size:9.5px; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
  padding:5px 11px; line-height:1.4;
}
.langsw button + button{border-left:1px solid var(--ink)}
.langsw button[aria-pressed="true"]{background:var(--red); color:var(--onred)}
.langsw button:hover:not([aria-pressed="true"]){background:var(--shade)}
.themesw{
  appearance:none; cursor:pointer; font:inherit; font-size:9.5px; font-weight:700;
  letter-spacing:.12em; text-transform:uppercase; padding:5px 12px; line-height:1.4;
  border:1px solid var(--ink); border-radius:999px;
  background:transparent; color:var(--ink);
}
.themesw:hover{background:var(--shade)}
.top .ctrls{display:flex; align-items:center; gap:10px}
.src{
  display:inline-block; margin-top:9px; color:var(--red); text-decoration:none;
  font-size:9.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
  border-bottom:1px solid transparent; padding-bottom:1px;
}
.src:hover,.src:focus-visible{border-bottom-color:var(--red)}
:focus-visible{outline:2px solid var(--red); outline-offset:3px}

.foot{background:var(--footer); color:var(--footer-ink); margin-top:52px; padding:38px 0 44px}
.foot .shell{display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; align-items:center}
.foot .wordmark{font-family:"Archivo Black",Impact,sans-serif; font-size:19px; letter-spacing:.02em; text-transform:uppercase}
.foot .note{font-size:10px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; opacity:.62}
"""


def esc(s): return html.escape(s, quote=False)


def photo(it, kind):
    if it.get("img"):
        return '<figure class="ph ph-%s"><img src="%s" alt="" loading="lazy"></figure>' % (
            kind, esc(it["img"]))
    bg, fg = SWATCH.get(it.get("tag", "").strip().lower(), DEFAULT_SWATCH)
    return ('<figure class="ph ph-%s fb" style="background:%s;color:%s">'
            '<span>%s</span></figure>') % (kind, bg, fg, esc(it.get("tag", "News")))


def article(it, kind):
    langs = "" if kind == "side" else "".join(
        '<p class="tx %s">%s</p>' % (k, esc(it[k]))
        for k in ("en", "zh", "ko") if it.get(k))
    return (
        '<article class="a-{k}">{ph}<span class="tag">{tag}</span>'
        '<h3 class="hl">{t}</h3>{langs}'
        '<a class="src" href="{url}" target="_blank" rel="noopener">{src} &rarr;</a></article>'
    ).format(k=kind, ph=photo(it, kind), tag=esc(it.get("tag", "News")), t=esc(it["t"]),
             langs=langs, url=esc(it["url"]), src=esc(it["src"]))


def render():
    files = sorted(glob.glob(os.path.join(DATA, "*.json")), reverse=True)
    days, total = [], 0
    for f in files:
        d = os.path.basename(f)[:-5]
        items = json.load(open(f))
        total += len(items)
        days.append((d, items))

    nav = "".join('<a href="#d%s">%s</a>' % (d, d[5:]) for d, _ in days[:7])

    body = []
    for d, items in days:
        y, m, dd = (int(x) for x in d.split("-"))
        wd = _date(y, m, dd).strftime("%A")
        lead = article(items[0], "lead") if items else ""
        mid = "".join(article(i, "mid") for i in items[1:3])
        side = "".join(article(i, "side") for i in items[3:6])
        foot = "".join(article(i, "foot") for i in items[6:10])
        band = ('<div class="band">'
                '<div class="col lead">{lead}</div>'
                '<div class="col mid">{mid}</div>'
                '<div class="col side">{side}</div>'
                '</div>').format(lead=lead, mid=mid, side=side)
        body.append(
            '<section class="day" id="d{d}">'
            '<div class="dayhead"><h2>{d}</h2><span class="rule"></span>'
            '<span class="meta">{wd} &middot; {n} stories</span></div>'
            '{band}{footrow}</section>'.format(
                d=d, wd=wd, n=len(items), band=band,
                footrow='<div class="foot-row">%s</div>' % foot if foot else "")
        )

    latest = days[0][0] if days else "—"
    return """<title>HMI Daily</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Archivo+Black&family=Newsreader:opsz,wght@6..72,400;6..72,600;6..72,700&display=swap">
<style>%s</style>
<div class="sheet">
<div class="shell">
  <div class="top">
    <span class="wordmark">HMI&nbsp;DAILY</span>
    <span class="nav">%s</span>
    <span class="ctrls">
      <span class="langsw" role="group" aria-label="Language">
        <button type="button" data-set="en" aria-pressed="true">EN</button>
        <button type="button" data-set="zh" aria-pressed="false">中文</button>
        <button type="button" data-set="ko" aria-pressed="false">한국어</button>
      </span>
      <button type="button" class="themesw" id="themesw" aria-label="Toggle colour theme">Dark</button>
    </span>
  </div>
  <header class="masthead">
    <h1>Latest News</h1>
    <div class="kicker">Cockpit &middot; Micromobility &middot; Interaction &middot; AI</div>
  </header>
  %s
</div>
</div>
<footer class="foot"><div class="shell">
  <span class="wordmark">HMI Daily</span>
  <span class="note">%d stories &middot; %d editions &middot; latest %s</span>
  <span class="note">Curated by Claude</span>
</div></footer>
<script>
(function(){
  var root=document.documentElement,btns=[].slice.call(document.querySelectorAll('.langsw button'));
  function apply(l){
    root.setAttribute('data-lang',l);
    btns.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.set===l));});
    try{localStorage.setItem('hmi-lang',l);}catch(e){}
  }
  var saved='en';
  try{saved=localStorage.getItem('hmi-lang')||'en';}catch(e){}
  apply(['en','zh','ko'].indexOf(saved)>-1?saved:'en');
  btns.forEach(function(b){b.addEventListener('click',function(){apply(b.dataset.set);});});

  var sw=document.getElementById('themesw');
  function prefersDark(){
    try{return window.matchMedia('(prefers-color-scheme: dark)').matches;}catch(e){return false;}
  }
  function paint(t){
    root.setAttribute('data-theme',t);
    if(sw) sw.textContent = (t==='dark' ? 'Light' : 'Dark');
    try{localStorage.setItem('hmi-theme',t);}catch(e){}
  }
  var st=null;
  try{st=localStorage.getItem('hmi-theme');}catch(e){}
  if(st==='dark'||st==='light'){ paint(st); }
  else if(sw){ sw.textContent = prefersDark() ? 'Light' : 'Dark'; }
  if(sw) sw.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    if(!cur) cur = prefersDark() ? 'dark' : 'light';
    paint(cur==='dark'?'light':'dark');
  });
})();
</script>""" % (CSS, nav, "".join(body), total, len(days), latest)


if __name__ == "__main__":
    page = render()
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width,initial-scale=1">'
               + page.replace("<style>", "</head><body><style>", 1) + "</body></html>")
        open(os.path.join(HERE, "index.html"), "w").write(doc)
        print("wrote index.html")
    else:
        open(os.path.join(HERE, "artifact.html"), "w").write(page)
        print("wrote artifact.html")
