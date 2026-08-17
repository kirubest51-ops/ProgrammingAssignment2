#!/usr/bin/env python3
"""Convert the Ethiopia report markdown into a designed standalone HTML artifact."""
import re, html, json, pathlib

import sys

REPORTS = {
 "map": dict(
   src="ETHIOPIA_OPPORTUNITY_REPORT_2026.md",
   out="ethiopia-opportunity-map.html",
   title="What Ethiopia Is Finally Ready For",
   eyebrow=["Opportunity map", "August 2026", "Independent analysis"],
   sub="Thirty proven business models tested against the thresholds Ethiopia has just crossed "
       "&mdash; and the ten whose adoption curve is about to begin.",
   meta=["19 sections", "30 candidates &middot; 15 ranked &middot; 10 deep dives", "~25,000 words"],
   stats=[("60.6M","telebirr users","ETB 4.19tn moved in FY2025/26"),
          ("~15%","smartphone penetration","the binding constraint on every consumer app"),
          ("551K","ETHQR transactions, ever","merchant acceptance has not started"),
          ("50M+","Fayda digital IDs","mandatory for banking from 2026"),
          ("22%","of remittances are formal","$7.17bn formal; the rest is hawala")],
 ),
 "spain": dict(
   src="SPAIN_ORAL_ELDERCARE_FOUNDER_REPORT.md",
   out="spain-oral-eldercare-map.html",
   title="The Mouth Nobody Checks",
   eyebrow=["Founder-fit assessment", "Spain &middot; oral health &amp; eldercare", "August 2026"],
   sub="A &euro;128m public programme has just reached older people in care homes, and reached "
       "3% of them. This is what a dental hygienist could build in that gap.",
   meta=["Third in the series", "8 candidates &middot; 5 deep dives", "~7,500 words"],
   stats=[("&euro;128M","newly allocated to oral health","&euro;68m for 2025 plus &euro;60m in May 2026"),
          ("~3%","of over-65s covered so far","against 30.4% of children"),
          ("407,780","residential care places","across 5,530 homes in Spain"),
          ("1 in 4","decayed teeth treated","in Spanish older adults"),
          ("~35%","of the market, 10 operators","a buyer list you can phone")],
 ),
 "founder": dict(
   src="ETHIOPIA_HEALTH_EDUCATION_FOUNDER_REPORT.md",
   out="ethiopia-clinician-founder-map.html",
   title="The Clinician&rsquo;s Unfair Advantage",
   eyebrow=["Founder-fit assessment", "Health &amp; education", "August 2026"],
   sub="Ethiopian health and education opportunities scored twice &mdash; once on market "
       "attractiveness, once on whether this particular founder can actually build them.",
   meta=["Companion to the opportunity map", "12 candidates &middot; 5 deep dives", "~11,000 words"],
   stats=[("8.4%","grade 12 pass rate","536,953 students failed in one year"),
          ("17.2%","private HEI exit-exam pass","against 62.37% for public universities"),
          ("$2bn","Mercor annualised revenue","up from ~$760m six months earlier"),
          ("14,080","subscribers already owned","the scarce asset, not the medical degree"),
          ("100%","FX retention since Feb 2026","what makes services export viable")],
 ),
}
CFG = REPORTS[sys.argv[1] if len(sys.argv) > 1 else "map"]
BASE = pathlib.Path(__file__).resolve().parent
SRC, OUT = BASE / CFG["src"], BASE / CFG["out"]

md = SRC.read_text(encoding="utf-8")

# ---------- inline ----------
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)',
               r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\w)', r'<em>\1</em>', t)
    # evidence chips
    t = re.sub(r'\[(V|E|A|I)\]', lambda m: f'<span class="ev ev-{m.group(1)}" title="{EV[m.group(1)]}">{m.group(1)}</span>', t)
    t = re.sub(r'\[(A/E|E/A|V/E|V/I|A|I)\s*&mdash;', r'[\1 —', t)
    return t

EV = {"V": "Verified — sourced", "E": "Estimate — derived", "A": "Assumption — stated input", "I": "Inference — judgement"}

def slug(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'[^a-zA-Z0-9\s-]', '', s).strip().lower()
    return re.sub(r'[\s-]+', '-', s)[:70]

# ---------- block parse ----------
lines = md.split("\n")
out, toc = [], []
i, n = 0, len(lines)

def close(stack):
    while stack:
        out.append(f"</{stack.pop()}>")

liststack = []

while i < n:
    ln = lines[i]

    # fenced code block
    if ln.startswith("```"):
        close(liststack)
        i += 1
        buf = []
        while i < n and not lines[i].startswith("```"):
            buf.append(lines[i]); i += 1
        i += 1
        out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
        continue

    # table
    if ln.startswith("|") and i + 1 < n and re.match(r'^\|[\s:|-]+\|$', lines[i + 1].strip()):
        close(liststack)
        def cells(row):
            return [c.strip() for c in row.strip().strip("|").split("|")]
        head = cells(ln)
        i += 2
        body = []
        while i < n and lines[i].startswith("|"):
            body.append(cells(lines[i])); i += 1
        wide = " wide" if len(head) > 7 else ""
        t = [f'<div class="tw{wide}"><table><thead><tr>']
        for c in head:
            t.append(f"<th>{inline(c)}</th>")
        t.append("</tr></thead><tbody>")
        for r in body:
            t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r[:len(head)]) + "</tr>")
        t.append("</tbody></table></div>")
        out.append("".join(t))
        continue

    # headings
    m = re.match(r'^(#{1,4})\s+(.*)$', ln)
    if m:
        close(liststack)
        lvl, txt = len(m.group(1)), m.group(2).strip()
        sid = slug(txt)
        if lvl == 1:
            num = re.match(r'^(\d+)\.\s*(.*)$', txt)
            if num:
                toc.append((num.group(1), num.group(2), sid))
                out.append(f'<h2 id="{sid}" class="sec"><span class="secnum">{num.group(1)}</span>'
                           f'<span class="sectxt">{inline(num.group(2))}</span></h2>')
            else:
                toc.append(("", txt, sid))
                out.append(f'<h2 id="{sid}" class="sec sec-plain">{inline(txt)}</h2>')
        elif lvl == 2:
            out.append(f'<h3 id="{sid}">{inline(txt)}</h3>')
        elif lvl == 3:
            out.append(f'<h4 id="{sid}">{inline(txt)}</h4>')
        else:
            out.append(f'<h5>{inline(txt)}</h5>')
        i += 1
        continue

    if re.match(r'^---+\s*$', ln):
        close(liststack); out.append('<hr />'); i += 1; continue

    # blockquote (may span, may contain ## heading)
    if ln.startswith(">"):
        close(liststack)
        buf = []
        while i < n and lines[i].startswith(">"):
            buf.append(lines[i].lstrip(">").strip()); i += 1
        inner = " ".join(x for x in buf if x)
        inner = re.sub(r'^#+\s*', '', inner)
        out.append(f'<blockquote><p>{inline(inner)}</p></blockquote>')
        continue

    # lists
    mu = re.match(r'^(\s*)([-*])\s+(.*)$', ln)
    mo = re.match(r'^(\s*)(\d+)\.\s+(.*)$', ln)
    if mu or mo:
        tag = "ul" if mu else "ol"
        txt = (mu or mo).group(3)
        if not liststack:
            out.append(f"<{tag}>"); liststack.append(tag)
        elif liststack[-1] != tag:
            close(liststack); out.append(f"<{tag}>"); liststack.append(tag)
        out.append(f"<li>{inline(txt)}</li>")
        i += 1
        continue

    if not ln.strip():
        close(liststack); i += 1; continue

    # paragraph
    close(liststack)
    buf = [ln]
    i += 1
    while i < n and lines[i].strip() and not re.match(r'^(#{1,4}\s|>|\||```|---+\s*$|\s*[-*]\s|\s*\d+\.\s)', lines[i]):
        buf.append(lines[i]); i += 1
    p = inline(" ".join(x.strip() for x in buf))
    cls = ' class="lede"' if p.startswith("<strong>") and len(p) > 260 else ""
    out.append(f"<p{cls}>{p}</p>")

close(liststack)
body_html = "\n".join(out)

# strip the source doc's own masthead (first h2 + subtitle) — replaced by designed header
body_html = re.sub(r'^.*?<hr />', '', body_html, count=1, flags=re.S)

nav = "\n".join(
    f'<a class="tocitem" href="#{s}"><span class="tocnum">{num or "·"}</span><span>{html.escape(t)}</span></a>'
    for num, t, s in toc)

STATS = CFG["stats"]
stats = "\n".join(
    f'<div class="stat"><div class="statv">{v}</div><div class="statl">{l}</div><div class="statn">{n_}</div></div>'
    for v, l, n_ in STATS)

CSS = r"""
:root{
  --paper:#FBFBF9; --surface:#F2F4EF; --surface2:#E9ECE5;
  --ink:#161B19; --muted:#5F6A64; --faint:#8A948E;
  --rule:#DBE0D8; --rule2:#C6CDC2;
  --accent:#0E6A4E; --accent-soft:#DCEDE4; --accent-ink:#0B5540;
  --flag:#9B3B2F; --flag-soft:#F6E4E0;
  --shadow:0 1px 2px rgba(20,30,25,.05),0 8px 28px -18px rgba(20,30,25,.28);
  --sans:"Helvetica Neue",Helvetica,Arial,system-ui,sans-serif;
  --serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#0E1311; --surface:#151C18; --surface2:#1C2521;
    --ink:#E6EBE7; --muted:#9BA69F; --faint:#75817A;
    --rule:#232D28; --rule2:#33403A;
    --accent:#59C79A; --accent-soft:#12291F; --accent-ink:#8FDCBB;
    --flag:#E29383; --flag-soft:#2C1A16;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -18px rgba(0,0,0,.7);
  }
}
:root[data-theme="dark"]{
  --paper:#0E1311; --surface:#151C18; --surface2:#1C2521;
  --ink:#E6EBE7; --muted:#9BA69F; --faint:#75817A;
  --rule:#232D28; --rule2:#33403A;
  --accent:#59C79A; --accent-soft:#12291F; --accent-ink:#8FDCBB;
  --flag:#E29383; --flag-soft:#2C1A16;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -18px rgba(0,0,0,.7);
}
*{box-sizing:border-box}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--serif); font-size:17px; line-height:1.66;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
.shell{display:grid; grid-template-columns:minmax(0,1fr); }
@media (min-width:1080px){
  .shell{grid-template-columns:276px minmax(0,1fr); align-items:start;}
}

/* ---- index rail ---- */
.rail{
  border-bottom:1px solid var(--rule); background:var(--surface);
  padding:20px 22px 22px;
}
@media (min-width:1080px){
  .rail{
    position:sticky; top:0; height:100vh; overflow-y:auto;
    border-bottom:0; border-right:1px solid var(--rule); padding:34px 24px 40px;
  }
}
.raillabel{
  font-family:var(--mono); font-size:10px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--faint); margin:0 0 14px;
}
.tocitem{
  display:flex; gap:11px; align-items:baseline; text-decoration:none;
  color:var(--muted); font-family:var(--sans); font-size:12.5px; line-height:1.35;
  padding:5px 8px 5px 6px; border-radius:4px; border-left:2px solid transparent;
}
.tocitem:hover{color:var(--ink); background:var(--surface2); border-left-color:var(--accent);}
.tocnum{
  font-family:var(--mono); font-size:10.5px; color:var(--faint);
  min-width:16px; font-variant-numeric:tabular-nums;
}
.tocitem:hover .tocnum{color:var(--accent);}

/* ---- main ---- */
main{padding:0 22px 96px; min-width:0;}
.col{max-width:69ch; margin:0 auto;}
@media (min-width:1080px){ main{padding:0 48px 120px;} }

/* masthead */
.mast{
  max-width:69ch; margin:0 auto; padding:56px 0 34px; border-bottom:1px solid var(--rule);
}
.eyebrow{
  font-family:var(--mono); font-size:10.5px; letter-spacing:.19em; text-transform:uppercase;
  color:var(--accent); margin:0 0 20px; display:flex; gap:10px; flex-wrap:wrap;
}
.eyebrow span:not(:last-child)::after{content:"  /"; color:var(--faint);}
h1{
  font-family:var(--sans); font-weight:700; letter-spacing:-.028em; line-height:1.03;
  font-size:clamp(2.3rem,6.2vw,3.9rem); margin:0 0 20px; text-wrap:balance;
}
.sub{
  font-family:var(--serif); font-size:clamp(1.02rem,2.1vw,1.2rem); color:var(--muted);
  margin:0 0 26px; max-width:56ch; line-height:1.5;
}
.meta{
  font-family:var(--mono); font-size:11px; color:var(--faint); letter-spacing:.05em;
  display:flex; gap:18px; flex-wrap:wrap;
}

/* stat strip */
.stats{
  max-width:69ch; margin:0 auto; display:grid; gap:1px; background:var(--rule);
  border:1px solid var(--rule); border-radius:6px; overflow:hidden;
  grid-template-columns:repeat(auto-fit,minmax(158px,1fr));
  margin-top:34px; margin-bottom:8px;
}
.stat{background:var(--surface); padding:15px 16px 16px;}
.statv{
  font-family:var(--sans); font-weight:700; font-size:1.5rem; letter-spacing:-.02em;
  color:var(--accent); font-variant-numeric:tabular-nums; line-height:1.1;
}
.statl{
  font-family:var(--mono); font-size:10px; letter-spacing:.11em; text-transform:uppercase;
  color:var(--ink); margin-top:7px;
}
.statn{font-family:var(--serif); font-size:12.5px; color:var(--muted); margin-top:5px; line-height:1.4;}

/* headings */
h2.sec{
  font-family:var(--sans); font-weight:700; letter-spacing:-.022em; line-height:1.12;
  font-size:clamp(1.5rem,3.4vw,2.05rem); margin:76px 0 22px; text-wrap:balance;
  display:flex; gap:16px; align-items:baseline; scroll-margin-top:24px;
}
h2.sec .secnum{
  font-family:var(--mono); font-size:.72em; font-weight:400; color:var(--accent);
  font-variant-numeric:tabular-nums; flex:none;
  border-bottom:2px solid var(--accent); line-height:1; padding-bottom:3px;
}
h2.sec-plain{display:block;}
h3{
  font-family:var(--sans); font-weight:700; font-size:1.16rem; letter-spacing:-.012em;
  margin:48px 0 14px; line-height:1.28; text-wrap:balance; scroll-margin-top:24px;
}
h4{
  font-family:var(--mono); font-weight:600; font-size:.78rem; letter-spacing:.1em;
  text-transform:uppercase; color:var(--accent); margin:36px 0 10px; scroll-margin-top:24px;
}
h5{font-family:var(--sans); font-weight:700; font-size:1rem; margin:26px 0 8px;}

p{margin:0 0 17px;}
.col > p, .col > ul, .col > ol, .col > blockquote{max-width:69ch;}
p.lede{font-size:1.06rem;}
strong{font-weight:700;}
em{font-style:italic;}
a{color:var(--accent-ink); text-decoration:underline; text-underline-offset:2px; text-decoration-thickness:.5px; text-decoration-color:var(--rule2);}
a:hover{text-decoration-color:var(--accent);}
a:focus-visible,.tocitem:focus-visible{outline:2px solid var(--accent); outline-offset:3px; border-radius:2px;}
code{font-family:var(--mono); font-size:.86em; background:var(--surface2); padding:1px 5px; border-radius:3px;}
hr{border:0; border-top:1px solid var(--rule); margin:56px 0;}
ul,ol{margin:0 0 18px; padding-left:1.35em;}
li{margin-bottom:8px;}
li::marker{color:var(--faint); font-family:var(--mono); font-size:.85em;}
blockquote{
  margin:32px 0; padding:22px 26px; background:var(--accent-soft);
  border-left:3px solid var(--accent); border-radius:0 6px 6px 0;
}
blockquote p{
  margin:0; font-family:var(--sans); font-weight:700; font-size:1.22rem;
  letter-spacing:-.015em; line-height:1.34;
}

/* evidence chips */
.ev{
  font-family:var(--mono); font-size:9.5px; font-weight:600; letter-spacing:.06em;
  display:inline-block; padding:1px 4px; border-radius:3px; vertical-align:1.5px;
  background:var(--surface2); color:var(--muted); border:1px solid var(--rule);
  cursor:help;
}
.ev-V{background:var(--accent-soft); color:var(--accent-ink); border-color:transparent;}
.ev-A{background:var(--flag-soft); color:var(--flag); border-color:transparent;}

/* tables */
.tw{
  overflow-x:auto; margin:26px 0 30px; border:1px solid var(--rule);
  border-radius:6px; background:var(--surface); box-shadow:var(--shadow);
  -webkit-overflow-scrolling:touch;
}
@media (min-width:1180px){
  .tw{width:min(112%,1180px); margin-left:calc((100% - min(112%,1180px))/2);}
  .tw.wide{width:min(150%,1500px); margin-left:calc((100% - min(150%,1500px))/2);}
}
table{border-collapse:collapse; width:100%; font-family:var(--sans); font-size:12.8px; line-height:1.45;}
thead th{
  background:var(--surface2); text-align:left; font-weight:700; font-size:10.5px;
  letter-spacing:.08em; text-transform:uppercase; color:var(--muted);
  padding:11px 13px; border-bottom:1px solid var(--rule2); white-space:nowrap;
}
tbody td{
  padding:11px 13px; border-bottom:1px solid var(--rule); vertical-align:top;
  font-variant-numeric:tabular-nums;
}
tbody tr:last-child td{border-bottom:0;}
tbody tr:hover td{background:var(--surface2);}
tbody td:first-child{color:var(--ink);}
table strong{color:var(--accent-ink); font-weight:700;}
.wide table{font-size:11.6px;}
.wide tbody td{padding:8px 9px; text-align:center;}
.wide tbody td:first-child, .wide thead th:first-child{text-align:left; min-width:190px;}

pre{
  background:var(--surface2); border:1px solid var(--rule); border-radius:6px;
  padding:18px 20px; overflow-x:auto; margin:26px 0; line-height:1.5;
}
pre code{
  background:none; padding:0; font-size:12.5px; color:var(--muted);
  white-space:pre; font-family:var(--mono);
}

/* footer */
footer{
  max-width:69ch; margin:70px auto 0; padding-top:26px; border-top:1px solid var(--rule);
  font-family:var(--mono); font-size:11px; color:var(--faint); line-height:1.7;
}
@media (prefers-reduced-motion:reduce){*{animation:none!important; transition:none!important;}}
"""

HTML = f"""<title>{CFG["title"]}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>{CSS}</style>
<div class="shell">
  <nav class="rail" aria-label="Report contents">
    <p class="raillabel">Contents</p>
    {nav}
  </nav>
  <main>
    <header class="mast">
      <p class="eyebrow">{"".join(f"<span>{{x}}</span>" for x in CFG["eyebrow"])}</p>
      <h1>{CFG["title"]}</h1>
      <p class="sub">{CFG["sub"]}</p>
      <p class="meta">{"".join(f"<span>{{x}}</span>" for x in CFG["meta"])}</p>
    </header>
    <section class="stats" aria-label="The five numbers the thesis rests on">{stats}</section>
    <div class="col">
      {body_html}
      <footer>
        Evidence is tagged throughout: <span class="ev ev-V">V</span> verified &middot;
        <span class="ev ev-E">E</span> estimate &middot;
        <span class="ev ev-A">A</span> assumption &middot;
        <span class="ev ev-I">I</span> inference.<br />
        Forward-looking statements are estimates. Not investment advice.
      </footer>
    </div>
  </main>
</div>
"""

OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, len(HTML), "bytes;", len(toc), "sections;", HTML.count("<table>"), "tables")
