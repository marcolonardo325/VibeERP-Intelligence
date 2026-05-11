"""
Render Medium_Article_TfL_DigitalTwin_D365.md → site/index.html
Self-contained static page (Medium look-alike). Deploy the `site/` folder anywhere:
Azure Static Web Apps, GitHub Pages, Netlify, S3, etc.

Run:  python build_site.py
"""
import os
import markdown

BASE = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(BASE, "Medium_Article_TfL_DigitalTwin_D365.md")
OUT_DIR = os.path.join(BASE, "site")
os.makedirs(OUT_DIR, exist_ok=True)

CSS = """
:root { --ink:#242424; --muted:#6b6b6b; --rule:#e6e6e6; --accent:#1a8917; --code-bg:#f6f6f4; }
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#fff;color:var(--ink);
  font-family:'Charter','Georgia','Cambria',serif;font-size:20px;line-height:1.65}
.wrap{max-width:720px;margin:0 auto;padding:56px 24px 96px}
.byline{display:flex;align-items:center;gap:12px;margin:28px 0 40px;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:14px;color:var(--muted)}
.byline .avatar{width:44px;height:44px;border-radius:50%;
  background:linear-gradient(135deg,#1a8917,#0a4);color:#fff;
  display:flex;align-items:center;justify-content:center;font-weight:600;font-size:16px}
.byline strong{color:var(--ink);display:block;font-size:15px}
h1{font-family:'sohne','Helvetica Neue',Arial,sans-serif;font-weight:800;
  font-size:42px;line-height:1.15;letter-spacing:-0.02em;margin:0 0 12px}
h2{font-family:'sohne','Helvetica Neue',Arial,sans-serif;font-weight:700;
  font-size:30px;line-height:1.2;margin:56px 0 14px;letter-spacing:-0.015em}
h3{font-family:'sohne','Helvetica Neue',Arial,sans-serif;font-weight:700;
  font-size:22px;margin:36px 0 10px}
.subtitle{color:var(--muted);font-size:22px;line-height:1.35;margin:0 0 8px;font-style:italic}
p{margin:0 0 22px}
hr{border:0;border-top:1px solid var(--rule);margin:36px 0}
a{color:var(--ink);text-decoration:underline;text-underline-offset:3px}
a:hover{color:var(--accent)}
ul,ol{padding-left:26px;margin:0 0 24px}
li{margin:6px 0}
blockquote{border-left:3px solid var(--ink);margin:0 0 24px;padding:4px 0 4px 22px;font-style:italic}
code{font-family:'SF Mono','Menlo','Consolas',monospace;font-size:.85em;
  background:var(--code-bg);padding:2px 6px;border-radius:4px}
pre{background:var(--code-bg);border-radius:6px;padding:18px 20px;
  overflow-x:auto;margin:0 0 24px;font-size:14px;line-height:1.5}
pre code{background:transparent;padding:0;font-size:14px}
table{border-collapse:collapse;width:100%;margin:0 0 24px;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:16px}
th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--rule)}
th{font-weight:700}
.tag{display:inline-block;background:#f2f2f2;color:#444;padding:4px 12px;
  border-radius:100px;font-size:13px;margin:0 6px 6px 0;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.tags{margin:48px 0 0}
"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | Marco Lonardo</title>
<meta name="description" content="Real-time digital twin of the London Underground wired into Dynamics 365 F&O.">
<meta property="og:title" content="{title}">
<meta property="og:type" content="article">
<meta property="og:description" content="Real-time digital twin of the London Underground wired into Dynamics 365 F&O.">
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <div class="byline">
    <div class="avatar">ML</div>
    <div>
      <strong>Marco Lonardo</strong>
      <span>Solution Engineer @ Microsoft · 8 min read</span>
    </div>
  </div>
  {body}
  <div class="tags">
    <span class="tag">Microsoft Fabric</span>
    <span class="tag">D365 F&amp;O</span>
    <span class="tag">Digital Twin</span>
    <span class="tag">Real Time Analytics</span>
    <span class="tag">Python</span>
  </div>
</div>
</body>
</html>"""

with open(MD_FILE, "r", encoding="utf-8") as f:
    md = f.read()

title = md.splitlines()[0].lstrip("# ").strip()
body = markdown.markdown(md, extensions=["fenced_code", "tables", "nl2br"])
# Promote the first H2 (subtitle) to styled paragraph
body = body.replace("<h2>", "<p class='subtitle'>", 1).replace("</h2>", "</p>", 1)

with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(PAGE.format(title=title, css=CSS, body=body))

print(f"✅ Wrote {os.path.join(OUT_DIR, 'index.html')}")
