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
.masthead{padding:40px 0 26px; text-align:center; border-bottom:3px solid var(--ink)}
@media (max-width:700px){ .masthead{padding:28px 0 20px} .masthead .kicker{font-size:9.5px; letter-spacing:.14em} }
.masthead h1{
  font-family:"Archivo Black",Impact,sans-serif; margin:0;
  font-size:clamp(42px,10.5vw,116px); line-height:.85; letter-spacing:-.025em;
  text-transform:uppercase; text-wrap:balance;
}
.masthead .kicker{
  margin-top:14px; font-size:11px; font-weight:600; letter-spacing:.2em;
  text-transform:uppercase; color:var(--muted);
}

.day{padding:36px 0 6px; border-bottom:1px solid var(--hair)}
.dayhead{display:flex; align-items:baseline; gap:16px; margin-bottom:24px}
.dayhead h2{
  font-family:"Archivo Black",Impact,sans-serif; margin:0;
  font-size:clamp(22px,3.2vw,30px); letter-spacing:-.01em; font-variant-numeric:tabular-nums;
  text-transform:uppercase;
}
.dayhead .rule{flex:1; height:2px; background:var(--ink)}
.dayhead .meta{
  font-size:10px; font-weight:700; letter-spacing:.16em; text-transform:uppercase;
  color:var(--muted); white-space:nowrap;
}

.band{
  display:grid; grid-template-columns:1.55fr 1fr; gap:32px;
  padding-bottom:28px; margin-bottom:28px; border-bottom:1px solid var(--hair);
}
.rail{display:grid; gap:22px; align-content:start; border-left:1px solid var(--hair); padding-left:32px}
.grid{display:grid; grid-template-columns:repeat(3,1fr); gap:30px; padding-bottom:32px}
@media (max-width:920px){
  .band{grid-template-columns:1fr; gap:26px}
  .rail{border-left:0; padding-left:0; border-top:1px solid var(--hair); padding-top:24px;
        grid-template-columns:1fr 1fr}
  .grid{grid-template-columns:1fr 1fr; gap:26px}
}
@media (max-width:620px){
  .rail,.grid{grid-template-columns:1fr; gap:34px}
  .band{padding-bottom:22px; margin-bottom:22px}
  .rail{padding-top:30px; gap:34px}
  .a-rail .hl,.a-grid .hl{font-size:24px}
  .a-rail .tx,.a-grid .tx{font-size:15px; line-height:1.55}
  .ph-rail,.ph-grid{aspect-ratio:16/10}
  .a-lead .hl{font-size:30px}
  .dayhead{gap:12px}
}

.ph{margin:0 0 13px; overflow:hidden; background:var(--shade)}
.ph img{width:100%; height:100%; object-fit:cover}
.ph-lead{aspect-ratio:16/9}
.ph-rail{aspect-ratio:4/3}
.ph-grid{aspect-ratio:3/2}
.ph.fb{display:flex; align-items:flex-end; padding:14px}
.ph.fb span{
  font-family:"Archivo Black",Impact,sans-serif; text-transform:uppercase;
  line-height:.86; letter-spacing:-.02em; word-break:break-word;
}
.ph-lead.fb span{font-size:clamp(34px,5vw,60px)}
.ph-rail.fb span{font-size:26px}
.ph-grid.fb span{font-size:30px}

.tag{
  display:inline-flex; align-items:center; gap:6px;
  background:var(--red); color:var(--onred);
  font-size:9.5px; font-weight:700; letter-spacing:.13em; text-transform:uppercase;
  padding:4px 10px 4px 7px; border-radius:999px; margin-bottom:10px;
}
.tag::before{content:""; width:7px; height:7px; border-radius:50%; background:var(--onred); opacity:.9}
.a-grid .tag{background:transparent; color:var(--red); border:1px solid var(--red); padding:3px 10px 3px 7px}
.a-grid .tag::before{background:var(--red); opacity:1}
.hl{
  font-family:"Newsreader","Iowan Old Style",Georgia,"Songti SC","Apple SD Gothic Neo",serif;
  font-weight:600; margin:0 0 11px;
  line-height:1.12; letter-spacing:-.012em; text-wrap:balance;
}
.a-lead .hl{font-size:clamp(30px,3.7vw,44px); line-height:1.06}
.a-rail .hl{font-size:19px}
.a-grid .hl{font-size:22px}
.tx{display:none; margin:0; max-width:62ch}
.tx.en{display:block}
html[data-lang="zh"] .tx.en,html[data-lang="ko"] .tx.en{display:none}
html[data-lang="zh"] .tx.zh{display:block}
html[data-lang="ko"] .tx.ko{display:block}
.a-lead .tx{font-size:15.5px}
.a-rail .tx{font-size:12.5px; line-height:1.5}
.a-grid .tx{font-size:13.5px}

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
  display:inline-block; margin-top:12px; color:var(--red); text-decoration:none;
  font-size:10.5px; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
  border-bottom:2px solid transparent; padding-bottom:2px;
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
    langs = "".join('<p class="tx %s">%s</p>' % (k, esc(it[k]))
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
        rail = "".join(article(i, "rail") for i in items[1:3])
        grid = "".join(article(i, "grid") for i in items[3:])
        body.append(
            '<section class="day" id="d{d}">'
            '<div class="dayhead"><h2>{d}</h2><span class="rule"></span>'
            '<span class="meta">{wd} &middot; {n} stories</span></div>'
            '<div class="band">{lead}<div class="rail">{rail}</div></div>'
            '{gridwrap}</section>'.format(
                d=d, wd=wd, n=len(items), lead=lead, rail=rail,
                gridwrap='<div class="grid">%s</div>' % grid if grid else "")
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
    <h1>Interface<br>Intelligence</h1>
    <div class="kicker">Cockpit &middot; Micromobility &middot; Interaction &middot; AI &mdash; every working day</div>
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
