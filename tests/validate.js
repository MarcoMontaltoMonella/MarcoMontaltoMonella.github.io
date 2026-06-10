/**
 * Static site validation tests.
 *
 * Checks HTML structure, asset references, content correctness,
 * and absence of known legacy/placeholder issues.
 *
 * Run with: npm test
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    passed++;
    console.log(`  \x1b[32m✓\x1b[0m ${message}`);
  } else {
    failed++;
    console.log(`  \x1b[31m✗\x1b[0m ${message}`);
  }
}

function readFile(relPath) {
  return fs.readFileSync(path.join(ROOT, relPath), "utf-8");
}

function fileExists(relPath) {
  return fs.existsSync(path.join(ROOT, relPath));
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Extract root-relative asset paths from href/src attributes. */
function extractLocalPaths(html) {
  const matches = [];
  // Match root-relative paths like /css/style.css, /img/header-bg.jpg
  const re = /(?:href|src)=["'](\/[^"'#]+)["']/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    let p = m[1];
    // Skip external, protocol-relative, or fragment-only links
    if (p.startsWith("//") || p.startsWith("http")) continue;
    // Remove leading slash for filesystem check
    p = p.replace(/^\//, "");
    // Skip empty paths
    if (!p) continue;
    matches.push(p);
  }
  return matches;
}

// ===================================================================
console.log("\n=== Homepage (index.html) ===");
// ===================================================================
{
  const html = readFile("index.html");

  // Structure
  assert(html.includes("<!DOCTYPE html>"), "has DOCTYPE");
  assert(html.includes('<meta name="viewport"'), "has viewport meta");
  assert(html.includes("<title>Marco Montalto Monella</title>"), "has title");

  // Modern design — no old frameworks
  assert(html.includes("Inter"), "uses Inter font");
  assert(!html.includes("Kaushan"), "no Kaushan Script font");
  assert(!html.includes("bootstrap"), "no Bootstrap references");
  assert(!html.includes("jquery"), "no jQuery references");
  assert(html.includes("/css/style.css"), "uses new style.css");
  assert(html.includes("/js/main.js"), "uses new main.js");

  // GA4 only
  assert(html.includes("G-XXH6Y7X45B"), "includes GA4 tag");
  assert(!html.includes("UA-93253018-1"), "removed legacy Universal Analytics");

  // No IE8 shims
  assert(!html.includes("html5shiv"), "removed IE8 html5shiv");
  assert(!html.includes("respond.js"), "removed IE8 respond.js");

  // Empty sections removed
  assert(!html.includes('id="portfolio"'), "removed empty portfolio section");
  assert(!html.includes("sponsor-1"), "removed empty sponsors section");

  // Timeline updated
  assert(html.includes("2023"), "timeline includes recent years");
  assert(html.includes("Pure Storage"), "mentions Pure Storage");
  assert(html.includes("Meta"), "mentions Meta");

  // Uses root-relative paths (not absolute mmmarco.com URLs)
  assert(!html.includes("https://mmmarco.com/css"), "no absolute CSS paths");
  assert(!html.includes("https://mmmarco.com/js"), "no absolute JS paths");
  // Asset references must stay root-relative (portable). Absolute URLs in
  // structured data / canonical tags are expected and allowed.
  assert(
    !html.includes('src="https://mmmarco.com/img') &&
      !html.includes("url('https://mmmarco.com/img"),
    "no absolute image asset paths"
  );

  // Has navigation
  assert(html.includes("Blog"), "has Blog nav link");

  // Asset files exist
  const assets = extractLocalPaths(html);
  for (const asset of assets) {
    assert(fileExists(asset), `asset exists: ${asset}`);
  }
}

// ===================================================================
console.log("\n=== Blog (blog/index.html) ===");
// ===================================================================
{
  const html = readFile("blog/index.html");

  // Subtitle
  assert(!html.includes("Blog Description"), 'no placeholder subtitle');
  assert(html.includes("Thoughts on software engineering"), "has real blog subtitle");

  // Placeholder posts removed
  assert(!html.includes("Second post"), "removed placeholder post-02");
  assert(!html.includes("Third post"), "removed placeholder post-03");
  assert(!html.includes(">Posts<"), "removed Posts index entry");

  // Real post present
  assert(
    html.includes("How Claude Rebuilt This Website"),
    "has the Claude rebuild blog post"
  );

  // Modern design
  assert(html.includes("/css/style.css"), "uses new style.css");
  assert(!html.includes("bootstrap"), "no Bootstrap references");

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");

  // Has social links in footer
  assert(html.includes("fa-linkedin"), "footer has LinkedIn icon");
  assert(html.includes("fa-github"), "footer has GitHub icon");

  // No old analytics
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");

  // Root-relative paths
  assert(!html.includes("https://mmmarco.com/css"), "no absolute CSS paths");
}

// ===================================================================
console.log("\n=== About section (on homepage) ===");
// ===================================================================
{
  const html = readFile("index.html");

  // About section exists on homepage with anchor
  assert(html.includes('id="about"'), "homepage has #about anchor");
  assert(html.includes("Marco Montalto Monella"), "mentions name");
  assert(html.includes("Pure Storage"), "mentions current employer");
  assert(html.includes("Meta"), "mentions former employer");
  assert(html.includes("NYU"), "mentions education");

  // Standalone about page removed
  assert(!fileExists("about/index.html"), "no standalone /about/ page");
}

// ===================================================================
console.log("\n=== Contact (contact/index.html) ===");
// ===================================================================
{
  const html = readFile("contact/index.html");

  // Modern design
  assert(html.includes("/css/style.css"), "uses new style.css");
  assert(!html.includes("bootstrap"), "no Bootstrap references");

  // Has contact form
  assert(html.includes('id="contactForm"'), "has contact form");

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");

  // No old analytics
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");

  // Root-relative paths
  assert(!html.includes("https://mmmarco.com/css"), "no absolute CSS paths");
}

// ===================================================================
console.log("\n=== 404 Page (404.html) ===");
// ===================================================================
{
  const html = readFile("404.html");

  assert(html.includes("Page not found"), "shows 404 message");
  assert(html.includes("Go Home"), "has Go Home button");
  assert(!html.includes("html5shiv"), "no IE8 shims");
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");
  assert(!html.includes('id="portfolio"'), "no portfolio section");
  assert(html.includes("/css/style.css"), "uses new style.css");
}

// ===================================================================
console.log("\n=== Blog Post (post/how-claude-rebuilt-this-website) ===");
// ===================================================================
{
  const postPath = "post/how-claude-rebuilt-this-website/index.html";
  assert(fileExists(postPath), "blog post HTML exists");

  const html = readFile(postPath);

  // Modern design
  assert(html.includes("/css/style.css"), "uses new style.css");
  assert(!html.includes("bootstrap"), "no Bootstrap references");

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");

  // Has social links in footer
  assert(html.includes("fa-linkedin"), "footer has LinkedIn icon");
  assert(html.includes("fa-github"), "footer has GitHub icon");

  // Has GA4
  assert(html.includes("G-XXH6Y7X45B"), "has GA4 tag");
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");

  // Content
  assert(html.includes("Claude"), "mentions Claude in content");
  assert(html.includes("Back to Blog"), "has back to blog link");

  // Root-relative paths
  assert(!html.includes("https://mmmarco.com/css"), "no absolute CSS paths");
}

// ===================================================================
console.log("\n=== CSS (css/style.css) ===");
// ===================================================================
{
  const css = readFile("css/style.css");

  // Color palette
  assert(css.includes("#0d9488"), "uses teal primary color (#0d9488)");
  assert(css.includes("#1e293b"), "uses dark slate (#1e293b)");
  assert(css.includes("#5eead4"), "uses mint accent (#5eead4)");

  // No old Facebook blue
  assert(!css.includes("#3b5998"), "no Facebook blue (#3b5998)");

  // Modern font
  assert(css.includes("Inter"), "uses Inter font family");
  assert(!css.includes("Kaushan"), "no Kaushan Script");

  // Modern CSS features
  assert(css.includes("--color-primary"), "uses CSS custom properties");
  assert(css.includes("grid"), "uses CSS Grid");
  assert(css.includes("gradient"), "uses CSS gradients");
  assert(css.includes("box-shadow"), "uses box shadows");
  assert(css.includes("translateY"), "uses transforms for hover effects");
}

// ===================================================================
console.log("\n=== Hugo artifacts removed ===");
// ===================================================================
{
  assert(!fileExists("categories"), "no categories/ directory");
  assert(!fileExists("tags"), "no tags/ directory");
  assert(!fileExists("post/index.html"), "no post/index.html");
  assert(!fileExists("post/index.xml"), "no post/index.xml");
  assert(!fileExists("index.xml"), "no root index.xml");
  assert(!fileExists("post/page"), "no post/page/ directory");
}

// ===================================================================
console.log("\n=== SEO ===");
// ===================================================================
{
  assert(fileExists("robots.txt"), "robots.txt exists");
  const robots = readFile("robots.txt");
  assert(robots.includes("Sitemap:"), "robots.txt references sitemap");

  assert(fileExists("sitemap.xml"), "sitemap.xml exists");
  const sitemap = readFile("sitemap.xml");
  assert(sitemap.includes("<urlset"), "sitemap.xml is a valid urlset");
  assert(sitemap.includes("https://mmmarco.com/"), "sitemap lists homepage");
  assert(
    sitemap.includes("https://mmmarco.com/post/how-claude-rebuilt-this-website/"),
    "sitemap lists blog post"
  );

  const home = readFile("index.html");
  assert(
    home.includes('application/ld+json') && home.includes('"@type": "Person"'),
    "homepage has Person structured data"
  );
  assert(home.includes('rel="canonical"'), "homepage has canonical link");
}

// ===================================================================
console.log("\n=== Build system ===");
// ===================================================================
{
  assert(fileExists("build.py"), "build.py exists");
  assert(fileExists("_posts"), "_posts/ directory exists");
  assert(
    fileExists("_posts/2026-03-21-how-claude-rebuilt-this-website.md"),
    "first blog post markdown exists"
  );
}

// ===================================================================
// Summary
// ===================================================================
console.log(`\n${"=".repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log(`${"=".repeat(50)}\n`);

process.exit(failed > 0 ? 1 : 0);
