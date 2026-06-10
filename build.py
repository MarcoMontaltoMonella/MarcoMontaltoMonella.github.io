#!/usr/bin/env python3
"""
Simple blog builder — converts Markdown files in _posts/ to static HTML.

Usage:
    python3 build.py

Markdown files should be named: YYYY-MM-DD-slug.md
and contain YAML-like frontmatter:

    ---
    title: My Post Title
    description: A short description
    date: 2026-03-21
    ---

    Your markdown content here...
"""

import os
import re
import html
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "_posts"
OUTPUT_DIR = ROOT / "post"
BLOG_INDEX = ROOT / "blog" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
LLMS = ROOT / "llms.txt"
SITE_URL = "https://mmmarco.com"

# Static pages to include in the sitemap (path, change-frequency, priority)
STATIC_PAGES = [
    ("/", "monthly", "1.0"),
    ("/blog/", "weekly", "0.8"),
    ("/contact/", "yearly", "0.5"),
    ("/pgpkey.html", "yearly", "0.3"),
]


# ─── Minimal Markdown → HTML converter ───────────────────────────────────────

def md_to_html(text):
    """Convert Markdown to HTML. Handles the most common constructs."""
    lines = text.split("\n")
    out = []
    in_code_block = False
    in_list = False
    list_type = None
    paragraph = []

    def flush_paragraph():
        if paragraph:
            content = inline(" ".join(paragraph))
            out.append(f"<p>{content}</p>")
            paragraph.clear()

    def flush_list():
        nonlocal in_list, list_type
        if in_list:
            tag = "ol" if list_type == "ol" else "ul"
            out.append(f"</{tag}>")
            in_list = False
            list_type = None

    def inline(s):
        # Images (before links so ![...](...) isn't caught as a link)
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', s)
        # Links
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        # Bold + italic
        s = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", s)
        # Bold
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        # Italic
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        # Inline code
        s = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", s)
        # Line break
        s = re.sub(r"  $", "<br>", s)
        return s

    for line in lines:
        stripped = line.strip()

        # Fenced code blocks
        if stripped.startswith("```"):
            if in_code_block:
                out.append("</code></pre>")
                in_code_block = False
            else:
                flush_paragraph()
                flush_list()
                lang = stripped[3:].strip()
                out.append(f"<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            out.append(html.escape(line))
            continue

        # Blank line — end paragraph or list
        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m:
            flush_paragraph()
            flush_list()
            level = len(m.group(1))
            content = inline(m.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            out.append(f"<h{level} id=\"{slug}\">{content}</h{level}>")
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}$", stripped):
            flush_paragraph()
            flush_list()
            out.append("<hr>")
            continue

        # Blockquotes
        if stripped.startswith("> "):
            flush_paragraph()
            flush_list()
            content = inline(stripped[2:])
            out.append(f"<blockquote><p>{content}</p></blockquote>")
            continue

        # Unordered list
        m = re.match(r"^[-*+]\s+(.+)$", stripped)
        if m:
            flush_paragraph()
            if not in_list or list_type != "ul":
                flush_list()
                out.append("<ul>")
                in_list = True
                list_type = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue

        # Ordered list
        m = re.match(r"^\d+\.\s+(.+)$", stripped)
        if m:
            flush_paragraph()
            if not in_list or list_type != "ol":
                flush_list()
                out.append("<ol>")
                in_list = True
                list_type = "ol"
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue

        # Regular paragraph text
        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    if in_code_block:
        out.append("</code></pre>")

    return "\n".join(out)


# ─── Frontmatter parser ─────────────────────────────────────────────────────

def parse_post(filepath):
    """Parse a markdown file with YAML-like frontmatter."""
    text = filepath.read_text(encoding="utf-8")

    # Split frontmatter from content
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"No frontmatter found in {filepath}")

    # Parse simple key: value frontmatter
    meta = {}
    for line in m.group(1).strip().split("\n"):
        kv = line.split(":", 1)
        if len(kv) == 2:
            meta[kv[0].strip()] = kv[1].strip()

    content_md = m.group(2).strip()
    content_html = md_to_html(content_md)

    # Derive slug from filename: YYYY-MM-DD-slug.md → slug
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", filepath.stem)

    # Parse date
    date_str = meta.get("date", "")
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = date.strftime("%B %d, %Y")
    except ValueError:
        date_formatted = date_str
        date = datetime.min

    return {
        "title": meta.get("title", slug.replace("-", " ").title()),
        "description": meta.get("description", ""),
        "date": date,
        "date_formatted": date_formatted,
        "date_str": date_str,
        "slug": slug,
        "content": content_html,
    }


# ─── HTML templates ──────────────────────────────────────────────────────────

POST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{description}">
  <meta name="author" content="Marco Montalto Monella">
  <title>{title} — Marco Montalto Monella</title>

  <link rel="stylesheet" href="/css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">

  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXH6Y7X45B"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-XXH6Y7X45B');
  </script>
</head>

<body class="page-inner">

  <!-- Navigation -->
  <nav class="nav">
    <div class="nav__inner">
      <a class="nav__brand" href="/">mmmarco</a>
      <button class="nav__toggle" aria-label="Toggle navigation">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav__links">
        <li><a href="/">Home</a></li>
        <li><a href="/#about">About</a></li>
        <li><a href="/blog/">Blog</a></li>
        <li><a href="/contact/">Contact</a></li>
      </ul>
    </div>
  </nav>

  <!-- Hero -->
  <header class="hero hero--compact" style="background-image: url('/img/post-bg.jpg')">
    <div class="hero__content">
      <h1 class="hero__title">{title}</h1>
      <p class="hero__subtitle">{description}</p>
    </div>
  </header>

  <!-- Article -->
  <article class="article">
    <div class="article-meta">
      <span><svg class="icon icon--calendar" viewBox="0 0 1664 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M128 -128h288v288h-288v-288zM480 -128h320v288h-320v-288zM128 224h288v320h-288v-320zM480 224h320v320h-320v-320zM128 608h288v288h-288v-288zM864 -128h320v288h-320v-288zM480 608h320v288h-320v-288zM1248 -128h288v288h-288v-288zM864 224h320v320h-320v-320z
M512 1088v288q0 13 -9.5 22.5t-22.5 9.5h-64q-13 0 -22.5 -9.5t-9.5 -22.5v-288q0 -13 9.5 -22.5t22.5 -9.5h64q13 0 22.5 9.5t9.5 22.5zM1248 224h288v320h-288v-320zM864 608h320v288h-320v-288zM1248 608h288v288h-288v-288zM1280 1088v288q0 13 -9.5 22.5t-22.5 9.5h-64
q-13 0 -22.5 -9.5t-9.5 -22.5v-288q0 -13 9.5 -22.5t22.5 -9.5h64q13 0 22.5 9.5t9.5 22.5zM1664 1152v-1280q0 -52 -38 -90t-90 -38h-1408q-52 0 -90 38t-38 90v1280q0 52 38 90t90 38h128v96q0 66 47 113t113 47h64q66 0 113 -47t47 -113v-96h384v96q0 66 47 113t113 47
h64q66 0 113 -47t47 -113v-96h128q52 0 90 -38t38 -90z"/></svg> {date_formatted}</span>
      <span><svg class="icon icon--user" viewBox="0 0 1280 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M1280 137q0 -109 -62.5 -187t-150.5 -78h-854q-88 0 -150.5 78t-62.5 187q0 85 8.5 160.5t31.5 152t58.5 131t94 89t134.5 34.5q131 -128 313 -128t313 128q76 0 134.5 -34.5t94 -89t58.5 -131t31.5 -152t8.5 -160.5zM1024 1024q0 -159 -112.5 -271.5t-271.5 -112.5
t-271.5 112.5t-112.5 271.5t112.5 271.5t271.5 112.5t271.5 -112.5t112.5 -271.5z"/></svg> Marco Montalto Monella</span>
    </div>

    {content}

    <div class="article-nav">
      <a href="/blog/">&larr; Back to Blog</a>
    </div>
  </article>

  <!-- Footer -->
  <footer class="footer">
    <ul class="footer__social">
      <li><a href="mailto:contact@mmmarco.com" title="Email"><svg class="icon icon--envelope" viewBox="0 0 1792 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M1792 826v-794q0 -66 -47 -113t-113 -47h-1472q-66 0 -113 47t-47 113v794q44 -49 101 -87q362 -246 497 -345q57 -42 92.5 -65.5t94.5 -48t110 -24.5h1h1q51 0 110 24.5t94.5 48t92.5 65.5q170 123 498 345q57 39 100 87zM1792 1120q0 -79 -49 -151t-122 -123
q-376 -261 -468 -325q-10 -7 -42.5 -30.5t-54 -38t-52 -32.5t-57.5 -27t-50 -9h-1h-1q-23 0 -50 9t-57.5 27t-52 32.5t-54 38t-42.5 30.5q-91 64 -262 182.5t-205 142.5q-62 42 -117 115.5t-55 136.5q0 78 41.5 130t118.5 52h1472q65 0 112.5 -47t47.5 -113z"/></svg></a></li>
      <li><a href="https://www.linkedin.com/in/montaltomonellamarco/" title="LinkedIn"><svg class="icon icon--linkedin" viewBox="0 0 1792 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M349 911v-991h-330v991h330zM370 1217q1 -73 -50.5 -122t-135.5 -49h-2q-82 0 -132 49t-50 122q0 74 51.5 122.5t134.5 48.5t133 -48.5t51 -122.5zM1536 488v-568h-329v530q0 105 -40.5 164.5t-126.5 59.5q-63 0 -105.5 -34.5t-63.5 -85.5q-11 -30 -11 -81v-553h-329
q2 399 2 647t-1 296l-1 48h329v-144h-2q20 32 41 56t56.5 52t87 43.5t114.5 15.5q171 0 275 -113.5t104 -332.5z"/></svg></a></li>
      <li><a href="https://github.com/MarcoMontaltoMonella" title="GitHub"><svg class="icon icon--github" viewBox="0 0 1792 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M768 1408q209 0 385.5 -103t279.5 -279.5t103 -385.5q0 -251 -146.5 -451.5t-378.5 -277.5q-27 -5 -40 7t-13 30q0 3 0.5 76.5t0.5 134.5q0 97 -52 142q57 6 102.5 18t94 39t81 66.5t53 105t20.5 150.5q0 119 -79 206q37 91 -8 204q-28 9 -81 -11t-92 -44l-38 -24
q-93 26 -192 26t-192 -26q-16 11 -42.5 27t-83.5 38.5t-85 13.5q-45 -113 -8 -204q-79 -87 -79 -206q0 -85 20.5 -150t52.5 -105t80.5 -67t94 -39t102.5 -18q-39 -36 -49 -103q-21 -10 -45 -15t-57 -5t-65.5 21.5t-55.5 62.5q-19 32 -48.5 52t-49.5 24l-20 3q-21 0 -29 -4.5
t-5 -11.5t9 -14t13 -12l7 -5q22 -10 43.5 -38t31.5 -51l10 -23q13 -38 44 -61.5t67 -30t69.5 -7t55.5 3.5l23 4q0 -38 0.5 -88.5t0.5 -54.5q0 -18 -13 -30t-40 -7q-232 77 -378.5 277.5t-146.5 451.5q0 209 103 385.5t279.5 279.5t385.5 103zM291 305q3 7 -7 12
q-10 3 -13 -2q-3 -7 7 -12q9 -6 13 2zM322 271q7 5 -2 16q-10 9 -16 3q-7 -5 2 -16q10 -10 16 -3zM352 226q9 7 0 19q-8 13 -17 6q-9 -5 0 -18t17 -7zM394 184q8 8 -4 19q-12 12 -20 3q-9 -8 4 -19q12 -12 20 -3zM451 159q3 11 -13 16q-15 4 -19 -7t13 -15q15 -6 19 6z
M514 154q0 13 -17 11q-16 0 -16 -11q0 -13 17 -11q16 0 16 11zM572 164q-2 11 -18 9q-16 -3 -14 -15t18 -8t14 14z"/></svg></a></li>
    </ul>
    <p class="footer__copy">Published under the Apache License 2.0.</p>
  </footer>

  <script src="/js/main.js"></script>
</body>
</html>
"""


def generate_blog_index(posts):
    """Generate blog/index.html from a list of posts."""
    post_cards = []
    for p in posts:
        card = f"""\
        <a class="post-card" href="/post/{p['slug']}/">
          <h2 class="post-card__title">{html.escape(p['title'])}</h2>
          <p class="post-card__excerpt">{html.escape(p['description'])}</p>
          <div class="post-card__meta">
            <span><svg class="icon icon--calendar" viewBox="0 0 1664 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M128 -128h288v288h-288v-288zM480 -128h320v288h-320v-288zM128 224h288v320h-288v-320zM480 224h320v320h-320v-320zM128 608h288v288h-288v-288zM864 -128h320v288h-320v-288zM480 608h320v288h-320v-288zM1248 -128h288v288h-288v-288zM864 224h320v320h-320v-320z
M512 1088v288q0 13 -9.5 22.5t-22.5 9.5h-64q-13 0 -22.5 -9.5t-9.5 -22.5v-288q0 -13 9.5 -22.5t22.5 -9.5h64q13 0 22.5 9.5t9.5 22.5zM1248 224h288v320h-288v-320zM864 608h320v288h-320v-288zM1248 608h288v288h-288v-288zM1280 1088v288q0 13 -9.5 22.5t-22.5 9.5h-64
q-13 0 -22.5 -9.5t-9.5 -22.5v-288q0 -13 9.5 -22.5t22.5 -9.5h64q13 0 22.5 9.5t9.5 22.5zM1664 1152v-1280q0 -52 -38 -90t-90 -38h-1408q-52 0 -90 38t-38 90v1280q0 52 38 90t90 38h128v96q0 66 47 113t113 47h64q66 0 113 -47t47 -113v-96h384v96q0 66 47 113t113 47
h64q66 0 113 -47t47 -113v-96h128q52 0 90 -38t38 -90z"/></svg> {p['date_formatted']}</span>
          </div>
        </a>"""
        post_cards.append(card)

    cards_html = "\n".join(post_cards) if post_cards else """\
        <div style="text-align: center; padding: 48px 0;">
          <p class="text-muted" style="font-size: 1.1rem;">No posts yet. Stay tuned!</p>
        </div>"""

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Blog posts by Marco Montalto Monella — software engineering, technology, and more.">
  <meta name="author" content="Marco Montalto Monella">
  <title>Blog — Marco Montalto Monella</title>

  <link rel="stylesheet" href="/css/style.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">

  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXH6Y7X45B"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-XXH6Y7X45B');
  </script>
</head>

<body class="page-inner">

  <!-- Navigation -->
  <nav class="nav">
    <div class="nav__inner">
      <a class="nav__brand" href="/">mmmarco</a>
      <button class="nav__toggle" aria-label="Toggle navigation">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav__links">
        <li><a href="/">Home</a></li>
        <li><a href="/#about">About</a></li>
        <li><a href="/blog/" class="active">Blog</a></li>
        <li><a href="/contact/">Contact</a></li>
      </ul>
    </div>
  </nav>

  <!-- Hero -->
  <header class="hero hero--compact" style="background-image: url('/img/home-bg.jpg')">
    <div class="hero__content">
      <h1 class="hero__title">Blog</h1>
      <p class="hero__subtitle">Thoughts on software engineering, technology, and life</p>
    </div>
  </header>

  <!-- Posts -->
  <section class="section">
    <div class="container container--narrow">
      <div class="posts">
{cards_html}
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <ul class="footer__social">
      <li><a href="mailto:contact@mmmarco.com" title="Email"><svg class="icon icon--envelope" viewBox="0 0 1792 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M1792 826v-794q0 -66 -47 -113t-113 -47h-1472q-66 0 -113 47t-47 113v794q44 -49 101 -87q362 -246 497 -345q57 -42 92.5 -65.5t94.5 -48t110 -24.5h1h1q51 0 110 24.5t94.5 48t92.5 65.5q170 123 498 345q57 39 100 87zM1792 1120q0 -79 -49 -151t-122 -123
q-376 -261 -468 -325q-10 -7 -42.5 -30.5t-54 -38t-52 -32.5t-57.5 -27t-50 -9h-1h-1q-23 0 -50 9t-57.5 27t-52 32.5t-54 38t-42.5 30.5q-91 64 -262 182.5t-205 142.5q-62 42 -117 115.5t-55 136.5q0 78 41.5 130t118.5 52h1472q65 0 112.5 -47t47.5 -113z"/></svg></a></li>
      <li><a href="https://www.linkedin.com/in/montaltomonellamarco/" title="LinkedIn"><svg class="icon icon--linkedin" viewBox="0 0 1792 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M349 911v-991h-330v991h330zM370 1217q1 -73 -50.5 -122t-135.5 -49h-2q-82 0 -132 49t-50 122q0 74 51.5 122.5t134.5 48.5t133 -48.5t51 -122.5zM1536 488v-568h-329v530q0 105 -40.5 164.5t-126.5 59.5q-63 0 -105.5 -34.5t-63.5 -85.5q-11 -30 -11 -81v-553h-329
q2 399 2 647t-1 296l-1 48h329v-144h-2q20 32 41 56t56.5 52t87 43.5t114.5 15.5q171 0 275 -113.5t104 -332.5z"/></svg></a></li>
      <li><a href="https://github.com/MarcoMontaltoMonella" title="GitHub"><svg class="icon icon--github" viewBox="0 0 1792 1792" aria-hidden="true" focusable="false"><path transform="translate(0 1536) scale(1 -1)" d="M768 1408q209 0 385.5 -103t279.5 -279.5t103 -385.5q0 -251 -146.5 -451.5t-378.5 -277.5q-27 -5 -40 7t-13 30q0 3 0.5 76.5t0.5 134.5q0 97 -52 142q57 6 102.5 18t94 39t81 66.5t53 105t20.5 150.5q0 119 -79 206q37 91 -8 204q-28 9 -81 -11t-92 -44l-38 -24
q-93 26 -192 26t-192 -26q-16 11 -42.5 27t-83.5 38.5t-85 13.5q-45 -113 -8 -204q-79 -87 -79 -206q0 -85 20.5 -150t52.5 -105t80.5 -67t94 -39t102.5 -18q-39 -36 -49 -103q-21 -10 -45 -15t-57 -5t-65.5 21.5t-55.5 62.5q-19 32 -48.5 52t-49.5 24l-20 3q-21 0 -29 -4.5
t-5 -11.5t9 -14t13 -12l7 -5q22 -10 43.5 -38t31.5 -51l10 -23q13 -38 44 -61.5t67 -30t69.5 -7t55.5 3.5l23 4q0 -38 0.5 -88.5t0.5 -54.5q0 -18 -13 -30t-40 -7q-232 77 -378.5 277.5t-146.5 451.5q0 209 103 385.5t279.5 279.5t385.5 103zM291 305q3 7 -7 12
q-10 3 -13 -2q-3 -7 7 -12q9 -6 13 2zM322 271q7 5 -2 16q-10 9 -16 3q-7 -5 2 -16q10 -10 16 -3zM352 226q9 7 0 19q-8 13 -17 6q-9 -5 0 -18t17 -7zM394 184q8 8 -4 19q-12 12 -20 3q-9 -8 4 -19q12 -12 20 -3zM451 159q3 11 -13 16q-15 4 -19 -7t13 -15q15 -6 19 6z
M514 154q0 13 -17 11q-16 0 -16 -11q0 -13 17 -11q16 0 16 11zM572 164q-2 11 -18 9q-16 -3 -14 -15t18 -8t14 14z"/></svg></a></li>
    </ul>
    <p class="footer__copy">Published under the Apache License 2.0.</p>
  </footer>

  <script src="/js/main.js"></script>
</body>
</html>
"""


def generate_sitemap(posts):
    """Generate sitemap.xml from the static pages plus all blog posts."""
    today = datetime.now().strftime("%Y-%m-%d")
    urls = []

    for path, changefreq, priority in STATIC_PAGES:
        urls.append(
            "  <url>\n"
            f"    <loc>{SITE_URL}{path}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
        )

    for p in posts:
        lastmod = p["date_str"] if p["date"] != datetime.min else today
        urls.append(
            "  <url>\n"
            f"    <loc>{SITE_URL}/post/{p['slug']}/</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            "    <changefreq>yearly</changefreq>\n"
            "    <priority>0.7</priority>\n"
            "  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def generate_llms(posts):
    """Generate llms.txt — a Markdown map of the site for LLMs (llmstxt.org)."""
    post_lines = [
        f"- [{p['title']}]({SITE_URL}/post/{p['slug']}/): {p['description']}"
        for p in posts
    ] or ["- No posts yet."]

    return (
        "# Marco Montalto Monella\n\n"
        "> Personal website and blog of Marco Montalto Monella, a software "
        "engineer and multidisciplinary builder based in the San Francisco "
        "Bay Area. Currently at Pure Storage, formerly a Production Engineer "
        "on Core Data at Meta. Alumnus of NYU and Politecnico di Torino.\n\n"
        "Marco believes he can build anything tech, from large-scale software "
        "to hardware (sharpening his analog craft by learning wood carving on "
        "the side). Above all he has an insatiable desire to learn, and loves "
        "teaching and mentoring others. Beyond engineering he teaches "
        "handstands and yoga sculpt, is writing his first book, and is a "
        "passionate chef who "
        "invests in and advises Nonna Gnocchi because he believes in Italian "
        "cuisine. He cares about innovation, health, and the environment, and "
        "stays active with gymnastics, beach volleyball, and running.\n\n"
        "## Main pages\n\n"
        f"- [Home]({SITE_URL}/): Overview of who Marco is, what drives him, "
        "his journey, and how to get in touch.\n"
        f"- [Blog]({SITE_URL}/blog/): Thoughts on software engineering, "
        "technology, and life.\n"
        f"- [Contact]({SITE_URL}/contact/): Contact form for getting in touch.\n\n"
        "## Blog posts\n\n"
        + "\n".join(post_lines)
        + "\n\n## Optional\n\n"
        f"- [PGP/GPG public key]({SITE_URL}/pgpkey.html): Public key for "
        "sending Marco encrypted email.\n"
        "- [GitHub](https://github.com/MarcoMontaltoMonella): Marco's "
        "open-source code and projects.\n"
        "- [LinkedIn](https://www.linkedin.com/in/montaltomonellamarco): "
        "Professional background and experience.\n"
    )


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if not POSTS_DIR.exists():
        print(f"No _posts/ directory found. Create it and add .md files.")
        return

    # Find and parse all markdown posts
    md_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    if not md_files:
        print("No .md files found in _posts/")
        return

    posts = []
    for f in md_files:
        try:
            post = parse_post(f)
            posts.append(post)
            print(f"  Parsed: {f.name} → {post['title']}")
        except Exception as e:
            print(f"  Error parsing {f.name}: {e}")

    # Sort by date (newest first)
    posts.sort(key=lambda p: p["date"], reverse=True)

    # Generate individual post pages
    for post in posts:
        post_dir = OUTPUT_DIR / post["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)
        post_html = POST_TEMPLATE.format(**post)
        (post_dir / "index.html").write_text(post_html, encoding="utf-8")
        print(f"  Generated: post/{post['slug']}/index.html")

    # Generate blog listing
    BLOG_INDEX.parent.mkdir(parents=True, exist_ok=True)
    blog_html = generate_blog_index(posts)
    BLOG_INDEX.write_text(blog_html, encoding="utf-8")
    print(f"  Generated: blog/index.html ({len(posts)} post(s))")

    # Generate sitemap (static pages + posts)
    SITEMAP.write_text(generate_sitemap(posts), encoding="utf-8")
    print(f"  Generated: sitemap.xml ({len(STATIC_PAGES) + len(posts)} URL(s))")

    # Generate llms.txt (site map for LLMs)
    LLMS.write_text(generate_llms(posts), encoding="utf-8")
    print(f"  Generated: llms.txt")

    print(f"\nDone! {len(posts)} post(s) built.")


if __name__ == "__main__":
    main()
