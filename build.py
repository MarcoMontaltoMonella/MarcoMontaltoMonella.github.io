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
  <link rel="stylesheet" href="/font-awesome-v4.7.0/css/font-awesome.min.css">
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
      <span><i class="fa fa-calendar"></i> {date_formatted}</span>
      <span><i class="fa fa-user"></i> Marco Montalto Monella</span>
    </div>

    {content}

    <div class="article-nav">
      <a href="/blog/">&larr; Back to Blog</a>
    </div>
  </article>

  <!-- Footer -->
  <footer class="footer">
    <ul class="footer__social">
      <li><a href="mailto:contact@mmmarco.com" title="Email"><i class="fa fa-envelope"></i></a></li>
      <li><a href="https://www.linkedin.com/in/montaltomonellamarco/" title="LinkedIn"><i class="fa fa-linkedin"></i></a></li>
      <li><a href="https://github.com/MarcoMontaltoMonella" title="GitHub"><i class="fa fa-github"></i></a></li>
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
            <span><i class="fa fa-calendar"></i> {p['date_formatted']}</span>
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
  <link rel="stylesheet" href="/font-awesome-v4.7.0/css/font-awesome.min.css">
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
      <li><a href="mailto:contact@mmmarco.com" title="Email"><i class="fa fa-envelope"></i></a></li>
      <li><a href="https://www.linkedin.com/in/montaltomonellamarco/" title="LinkedIn"><i class="fa fa-linkedin"></i></a></li>
      <li><a href="https://github.com/MarcoMontaltoMonella" title="GitHub"><i class="fa fa-github"></i></a></li>
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

    print(f"\nDone! {len(posts)} post(s) built.")


if __name__ == "__main__":
    main()
