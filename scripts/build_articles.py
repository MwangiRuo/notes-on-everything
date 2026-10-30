#!/usr/bin/env python3
"""Generate indexable article pages and sitemap from Pages CMS Markdown posts."""
from pathlib import Path
from datetime import date
from html import escape
from urllib.parse import quote
import re
import shutil
import yaml
import markdown

ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "posts"
OUTPUT = ROOT / "articles"
BASE = "https://notes-on-everything.pages.dev"
EMAIL = "notesoneverything.blog@gmail.com"

def esc(value):
    return escape(str(value or ""), quote=True)

def parse_post(path):
    raw = path.read_text(encoding="utf-8")
    metadata = {}
    if raw.startswith("---"):
        parts = re.split(r"^---\s*$", raw, maxsplit=2, flags=re.MULTILINE)
        if len(parts) == 3:
            metadata = yaml.safe_load(parts[1]) or {}
            raw = parts[2].lstrip("\r\n")
    if metadata.get("draft") is True or metadata.get("published") is False:
        return None
    return metadata, raw

def render_page(slug, metadata, body):
    title = str(metadata.get("title") or slug.replace("-", " ").title())
    description = str(metadata.get("description") or metadata.get("excerpt") or "")
    date_value = str(metadata.get("date") or "")
    topic = str(metadata.get("topic") or "Notes")
    url = f"{BASE}/articles/{quote(slug)}/"
    article = markdown.markdown(body, extensions=["extra", "sane_lists"])
    subject = quote("Response to: " + title)
    structured = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": title, "description": description,
        "author": {"@type": "Person", "name": "Lenny Mwangi Ruo"},
        "mainEntityOfPage": url,
    }
    if date_value:
        structured["datePublished"] = date_value
    import json
    json_ld = json.dumps(structured, ensure_ascii=False).replace("<", "\\u003c")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Notes on Everything</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}">
<script type="application/ld+json">{json_ld}</script>
<style>
:root{{color-scheme:light dark}}*{{box-sizing:border-box}}
body{{margin:0;background:#f8f5ef;color:#302e2a;font:18px/1.85 Georgia,serif}}
header{{border-bottom:1px solid #ddd7cf;padding:22px max(24px,calc((100vw - 800px)/2));font-size:20px}}
a{{color:#a35c3e}}header a{{text-decoration:none;color:inherit}}
main{{max-width:720px;margin:75px auto 110px;padding:0 24px}}
h1{{font:normal clamp(34px,6vw,48px)/1.18 Georgia,serif;margin:18px 0}}
h2{{font-size:30px;line-height:1.3}}h3{{font-size:24px}}
.meta{{color:#8a7f74;font:12px Arial,sans-serif;letter-spacing:2px;text-transform:uppercase}}
.intro{{color:#756b62;font-size:22px}}.divider{{height:1px;background:#ded8cf;margin:38px 0}}
article img{{max-width:100%;height:auto}}article blockquote{{border-left:2px solid #a35c3e;padding-left:20px;margin-left:0;color:#756b62}}
article pre{{white-space:pre-wrap;overflow-wrap:anywhere;padding:16px;background:#eee9e2}}
.reply{{border-top:1px solid #ded8cf;margin-top:70px;padding-top:25px}}
footer{{text-align:center;padding:30px;border-top:1px solid #ddd7cf;font:12px Arial,sans-serif;color:#776e66}}
@media(prefers-color-scheme:dark){{body{{background:#242321;color:#e9e4dc}}a{{color:#e3a78b}}header,footer,.reply{{border-color:#504943}}.intro,.meta{{color:#b6aaa0}}article pre{{background:#34312e}}}}
</style></head>
<body><header><a href="/">Notes on Everything.</a></header>
<main><a href="/#/writing">← All writing</a>
<p class="meta">{esc(date_value)} · {esc(topic)}</p>
<h1>{esc(title)}</h1>
{f'<p class="intro">{esc(description)}</p>' if description else ''}
<div class="divider"></div><article>{article}</article>
<section class="reply"><h2>Write back.</h2><p>Thoughts, disagreements, or a note of your own? Your response is private and won't be published.</p>
<p><a href="https://mail.google.com/mail/?view=cm&amp;fs=1&amp;to=notesoneverything.blog%40gmail.com&amp;su={subject}" target="_blank" rel="noopener noreferrer">Respond privately using Gmail →</a></p>
<p><a href="mailto:{EMAIL}?subject={subject}">Use another email app</a></p>
</section></main><footer>© Notes on Everything · By Lenny Mwangi Ruo</footer></body></html>
"""

def main():
    OUTPUT.mkdir(exist_ok=True)
    # This directory is generated; remove pages for deleted/unpublished articles.
    for child in OUTPUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
    urls = [f"{BASE}/"]
    for path in sorted(POSTS.glob("*.md")) if POSTS.exists() else []:
        parsed = parse_post(path)
        if parsed is None:
            continue
        meta, body = parsed
        slug = path.stem
        directory = OUTPUT / slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(render_page(slug, meta, body), encoding="utf-8")
        urls.append(f"{BASE}/articles/{quote(slug)}/")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join(f"  <url><loc>{esc(url)}</loc></url>\n" for url in urls)
    xml += "</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"Generated {len(urls)-1} articles and sitemap.")

if __name__ == "__main__":
    main()
