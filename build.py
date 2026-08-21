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
# one hue per category — pill colour and photo-fallback panel
CAT = {
    "micromobility": "#E5342A",   # the desk's own beat rides the red
    "cockpit":       "#7B5CF0",
    "interaction":   "#17A472",
    "ai":            "#DB3A9C",
    "design":        "#E07A18",
    "visual":        "#2E6BE6",   # graphic / 2D / motion graphics
    "industrial":    "#B08900",   # product & industrial design, CMF
}
DEFAULT_CAT = "#5B5750"


def cat_colour(tag):
    return CAT.get((tag or "").strip().lower(), DEFAULT_CAT)

CSS = """
:root{
  --ground:#E3E2DD; --paper:#E3E2DD; --ink:#111110; --muted:#6A6862;
  --rule:#BFBCB2; --hair:#D1CFC6; --red:#E5342A; --onred:#FFFFFF;
  --footer:#151513; --footer-ink:#E3E2DD; --shade:#D7D6D0;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#111110; --paper:#111110; --ink:#EDEBE4; --muted:#918D83;
    --rule:#33322D; --hair:#2A2924; --red:#FF4A3D; --onred:#141412;
    --footer:#080807; --footer-ink:#EDEBE4; --shade:#1E1D1A;
  }
}
:root[data-theme="dark"]{
  --ground:#111110; --paper:#111110; --ink:#EDEBE4; --muted:#918D83;
  --rule:#33322D; --hair:#2A2924; --red:#FF4A3D; --onred:#141412;
  --footer:#080807; --footer-ink:#EDEBE4; --shade:#1E1D1A;
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"Helvetica Neue",Helvetica,-apple-system,BlinkMacSystemFont,Arial,"PingFang SC","Hiragino Sans GB","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased;
}
img{max-width:100%; display:block}
.sheet{max-width:1180px; margin:0 auto}
.shell{max-width:1180px; margin:0 auto; padding:0 34px}
@media (max-width:700px){ .shell{padding:0 20px} }

.top{
  display:flex; align-items:center; justify-content:space-between; gap:14px;
  padding:15px 0; border-bottom:1px solid var(--ink); flex-wrap:wrap;
  font-size:10px; font-weight:700; letter-spacing:.16em; text-transform:uppercase;
}
@media (max-width:700px){
  .top{gap:12px; padding:13px 0}
  .top .nav{order:3; width:100%; justify-content:flex-start; overflow-x:auto; gap:16px; padding-bottom:2px}
}
.top .wordmark{font-family:"Archivo Black",Impact,sans-serif; font-size:15px; letter-spacing:.02em}
.top .nav{display:flex; gap:18px; color:var(--muted); flex-wrap:wrap}
.top .nav a{color:inherit; text-decoration:none}
.top .nav a:hover{color:var(--red)}
.masthead{padding:36px 0 30px; text-align:center; border-bottom:1px solid var(--ink)}
.masthead h1{
  font-family:"Archivo Black",Impact,sans-serif; margin:0;
  font-size:clamp(36px,7.6vw,78px); line-height:.9; letter-spacing:-.035em;
  text-transform:uppercase; text-wrap:balance;
}
.masthead .kicker{
  margin-top:9px; font-size:9.5px; font-weight:600; letter-spacing:.18em;
  text-transform:uppercase; color:var(--muted);
}
@media (max-width:700px){ .masthead{padding:18px 0 14px} }

/* ---- date band ---- */
.day{padding:34px 0 12px}
.day + .day{border-top:2px solid var(--ink)}
.dayhead{display:flex; align-items:baseline; gap:14px; margin-bottom:24px}
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
.col{padding:22px 26px 30px; border-left:1px solid var(--hair); min-width:0}
.col:first-child{padding-left:0; border-left:0}
.col:last-child{padding-right:0}
.col.mid,.col.side{display:grid; gap:24px; align-content:start}
.col.mid > article + article{border-top:1px solid var(--hair); padding-top:24px}
.col.side{text-align:center}
.col.side .tagrow{margin-left:auto; margin-right:auto; display:flex; justify-content:center}
.col.side .tx{margin-left:auto; margin-right:auto}
.col.side > article + article{border-top:1px solid var(--hair); padding-top:24px}
.foot-row{
  display:grid; grid-template-columns:repeat(4,1fr); gap:0;
  border-top:1px solid var(--hair); margin-bottom:4px;
}
.foot-row:first-of-type{border-top:1px solid var(--ink)}
.foot-row > article{padding:22px 26px 30px; border-left:1px solid var(--hair); min-width:0}
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
  .col{padding:24px 0; border-left:0; border-top:1px solid var(--hair)}
  .col:first-child{border-top:0; padding-top:4px}
  .col.side{grid-template-columns:1fr}
  .col.side > article + article{border-left:0; padding-left:0;
            border-top:1px solid var(--hair); padding-top:24px}
  .foot-row{grid-template-columns:1fr}
  .foot-row > article{padding:24px 0; border-left:0; border-top:1px solid var(--hair)}
  .foot-row > article:first-child{border-top:0}
}

/* ---- photos ---- */
.ph{margin:0 0 14px; overflow:hidden; background:var(--shade)}
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
.tagrow{display:inline-flex; align-items:center; gap:7px; margin-bottom:10px}
.tag{
  display:inline-flex; align-items:center; gap:5px;
  background:transparent; color:var(--cat,var(--red));
  border:1px solid var(--cat,var(--red));
  font-size:8.5px; font-weight:700; letter-spacing:.11em; text-transform:uppercase;
  padding:2.5px 9px 2.5px 6px; border-radius:999px;
}
.tag::before{content:""; width:6px; height:6px; border-radius:50%; background:var(--cat,var(--red))}

/* ---- headlines & text ---- */
.hl{
  font-family:"Noto Serif Display","Times New Roman","Iowan Old Style",Georgia,"Songti SC","Apple SD Gothic Neo",serif;
  font-weight:550; font-stretch:80%; margin:0 0 10px;
  line-height:1.08; letter-spacing:-.01em; text-wrap:balance;
}
.a-lead .hl{font-size:clamp(30px,3.9vw,44px); line-height:1.05; margin-bottom:12px}
.a-mid .hl{font-size:clamp(22px,2.5vw,29px); line-height:1.1}
.a-side .hl{font-size:17px; line-height:1.2}
.a-foot .hl{font-size:20px; line-height:1.15}
.tx{display:none; margin:0; max-width:60ch; color:var(--ink)}
.tx.en{display:block}
html[data-lang="zh"] .tx.en,html[data-lang="ko"] .tx.en{display:none}
html[data-lang="zh"] .tx.zh{display:block}
html[data-lang="ko"] .tx.ko{display:block}
.a-lead .tx{font-size:14px; line-height:1.6; color:var(--muted)}
.a-mid .tx{font-size:13px; line-height:1.55; color:var(--muted)}
.a-foot .tx,.a-side .tx{font-size:12.5px; line-height:1.5; color:var(--muted)}
/* the reference runs headline-only in the narrow cells; keep that in English,
   but show the translated line when a reader picks 中文 / 한국어 */
html:not([data-lang="zh"]):not([data-lang="ko"]) .a-side .tx,
html:not([data-lang="zh"]):not([data-lang="ko"]) .a-foot .tx{display:none}
@media (max-width:660px){
  .a-side .hl,.a-foot .hl,.a-mid .hl{font-size:24px}
  .a-lead .hl{font-size:29px}
  .a-mid .tx,.a-foot .tx,.a-side .tx{font-size:14px}
  .ph-side{aspect-ratio:16/9}
  .col.side{text-align:left}
  .col.side .tagrow{margin-left:0; margin-right:0; justify-content:flex-start}
  .col.side .tx{margin-left:0; margin-right:0}
}

.ctrls{position:relative}
.menubtn{
  appearance:none; cursor:pointer; background:transparent; border:1px solid var(--ink);
  border-radius:999px; width:34px; height:28px; padding:0;
  display:inline-flex; align-items:center; justify-content:center; color:var(--ink);
}
.menubtn:hover{background:var(--shade)}
.menubtn svg{width:14px; height:14px; display:block}
.menu{
  position:absolute; right:0; top:calc(100% + 10px); z-index:60;
  background:var(--ground); border:1px solid var(--ink);
  padding:16px; display:grid; gap:14px; min-width:216px;
  box-shadow:0 10px 28px rgba(0,0,0,.14); text-align:left;
}
.menu[hidden]{display:none}
.menu-team{
  border-top:1px solid var(--hair); padding-top:13px; display:grid; gap:6px;
}
.menu-team .dedication{
  font-family:"Noto Serif Display","Times New Roman",Georgia,serif; font-style:italic;
  font-size:13px; color:var(--ink); text-transform:none; letter-spacing:0;
}
.menu-team .team-names{
  font-size:10.5px; font-weight:600; letter-spacing:.05em; color:var(--muted);
  text-transform:uppercase; line-height:1.7;
}
.menu .mlabel{
  display:block; font-size:9px; font-weight:700; letter-spacing:.16em;
  text-transform:uppercase; color:var(--muted); margin-bottom:7px;
}
.langsw{display:flex; gap:0; border:1px solid var(--ink); border-radius:999px; overflow:hidden}
.langsw button{flex:1 1 0}
.langsw button{
  appearance:none; border:0; background:transparent; color:var(--ink); cursor:pointer;
  font:inherit; font-size:9.5px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  padding:5px 10px; line-height:1.4; text-align:center; white-space:nowrap;
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

.morebar{
  display:block; margin:26px 0 8px; padding:15px; border-radius:999px;
  background:var(--ink); color:var(--ground); text-decoration:none; text-align:center;
  font-size:10px; font-weight:700; letter-spacing:.2em; text-transform:uppercase;
}
.morebar:hover{background:var(--red); color:#fff}
.foot{background:var(--footer); color:var(--footer-ink); margin-top:30px; padding:44px 0 50px}
.foot-grid{display:flex; justify-content:space-between; gap:18px; flex-wrap:wrap; align-items:center}
.foot .wordmark{font-family:"Archivo Black",Impact,sans-serif; font-size:19px; letter-spacing:.02em; text-transform:uppercase}
.foot .note{font-size:10px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; opacity:.62}
"""


def esc(s): return html.escape(s, quote=False)


def photo(it, kind):
    if it.get("img"):
        return '<figure class="ph ph-%s"><img src="%s" alt="" loading="lazy"></figure>' % (
            kind, esc(it["img"]))
    return ('<figure class="ph ph-%s fb" style="background:%s;color:#fff">'
            '<span>%s</span></figure>') % (
        kind, cat_colour(it.get("tag")), esc(it.get("tag", "News")))


def article(it, kind):
    langs = "".join('<p class="tx %s">%s</p>' % (k, esc(it[k]))
                    for k in ("en", "zh", "ko") if it.get(k))
    return (
        '<article class="a-{k}">{ph}'
        '<span class="tagrow" style="--cat:{c}">'
        '<span class="tag">{tag}</span></span>'
        '<h3 class="hl">{t}</h3>{langs}'
        '<a class="src" href="{url}" target="_blank" rel="noopener">{src} &rarr;</a></article>'
    ).format(k=kind, ph=photo(it, kind), c=cat_colour(it.get("tag")),
             tag=esc(it.get("tag", "News")), t=esc(it["t"]),
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
        rest = items[6:]
        rows = [rest[i:i + 4] for i in range(0, len(rest), 4)]
        foot = "".join(
            '<div class="foot-row">%s</div>' % "".join(article(i, "foot") for i in row)
            for row in rows)
        band = ('<div class="band">'
                '<div class="col lead">{lead}</div>'
                '<div class="col mid">{mid}</div>'
                '<div class="col side">{side}</div>'
                '</div>').format(lead=lead, mid=mid, side=side)
        body.append(
            '<section class="day" id="d{d}">'
            '<div class="dayhead"><h2>{d}</h2><span class="rule"></span>'
            '<span class="meta">{wd} &middot; {n} stories</span></div>'
            '{band}{foot}</section>'.format(
                d=d, wd=wd, n=len(items), band=band, foot=foot)
        )

    latest = days[0][0] if days else "—"
    return """<title>ADUX Daily</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Noto+Serif+Display:wdth,wght@62.5..100,400..700&display=swap">
<style>%s</style>
<div class="sheet" id="top">
<div class="shell">
  <div class="top">
    <span class="wordmark">ADUX&nbsp;DAILY</span>
    <span class="nav">%s</span>
    <span class="ctrls">
      <button type="button" class="menubtn" id="menubtn" aria-expanded="false" aria-label="Settings">
        <svg viewBox="0 0 16 16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M2 4h12M2 8h12M2 12h12"/></svg>
      </button>
      <div class="menu" id="menu" hidden>
        <div><span class="mlabel">Language</span>
          <span class="langsw" role="group" aria-label="Language">
            <button type="button" data-set="en" aria-pressed="false">EN</button>
            <button type="button" data-set="zh" aria-pressed="false">中文</button>
            <button type="button" data-set="ko" aria-pressed="false">한국어</button>
          </span>
        </div>
        <div><span class="mlabel">Theme</span>
          <button type="button" class="themesw" id="themesw" aria-label="Toggle colour theme">Dark</button>
        </div>
        <div class="menu-team">
          <span class="dedication">for DC Advanced UX Team.</span>
          <span class="team-names">Vivi &middot; Yohan &middot; Libby &middot; Lim<br>Jisu &middot; Katey &middot; Anna</span>
        </div>
      </div>
    </span>
  </div>
  <header class="masthead">
    <h1>Latest News</h1>
    <div class="kicker">Micromobility &middot; Cockpit &middot; Interaction &middot; AI &middot; Design</div>
  </header>
  %s
  <a class="morebar" href="#top">Back to top &uarr;</a>
</div>
</div>
<footer class="foot"><div class="shell foot-grid">
  <span class="wordmark">ADUX Daily</span>
  <span class="note">%d stories &middot; %d editions &middot; latest %s</span>
  <span class="note">Curated by Claude</span>
</div></footer>
<script>
(function(){
  var root=document.documentElement;
  var btns=[].slice.call(document.querySelectorAll('.langsw button'));
  var sw=document.getElementById('themesw');
  var mb=document.getElementById('menubtn'), menu=document.getElementById('menu');

  /* ---- language: stored choice, else the device language ---- */
  function applyLang(l,store){
    root.setAttribute('data-lang',l);
    btns.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.set===l));});
    if(store){try{localStorage.setItem('hmi-lang',l);}catch(e){}}
  }
  var lang=null;
  try{lang=localStorage.getItem('hmi-lang');}catch(e){}
  if(['en','zh','ko'].indexOf(lang)<0){
    var nav=(navigator.language||'en').toLowerCase();
    lang=nav.indexOf('ko')===0?'ko':nav.indexOf('zh')===0?'zh':'en';
  }
  applyLang(lang,false);
  btns.forEach(function(b){b.addEventListener('click',function(){applyLang(b.dataset.set,true);});});

  /* ---- theme: stored choice, else the device setting (via media query) ---- */
  function systemDark(){
    try{return window.matchMedia('(prefers-color-scheme: dark)').matches;}catch(e){return false;}
  }
  function label(){
    var cur=root.getAttribute('data-theme');
    var dark=cur? cur==='dark' : systemDark();
    if(sw) sw.textContent=dark?'Light':'Dark';
  }
  var th=null;
  try{th=localStorage.getItem('hmi-theme');}catch(e){}
  if(th==='dark'||th==='light'){ root.setAttribute('data-theme',th); }
  label();
  if(sw) sw.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    var dark=cur? cur==='dark' : systemDark();
    var next=dark?'light':'dark';
    root.setAttribute('data-theme',next);
    try{localStorage.setItem('hmi-theme',next);}catch(e){}
    label();
  });

  /* ---- hamburger ---- */
  function setMenu(open){
    if(!menu||!mb) return;
    menu.hidden=!open;
    mb.setAttribute('aria-expanded',String(open));
  }
  if(mb) mb.addEventListener('click',function(e){e.stopPropagation(); setMenu(menu.hidden);});
  document.addEventListener('click',function(e){
    if(menu&&!menu.hidden&&!menu.contains(e.target)) setMenu(false);
  });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') setMenu(false); });
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
