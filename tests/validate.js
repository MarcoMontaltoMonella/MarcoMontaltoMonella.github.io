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

/** Extract all local asset paths (CSS, JS, images) from href/src attributes. */
function extractLocalPaths(html) {
  const matches = [];
  const re = /(?:href|src)=["']https:\/\/mmmarco\.com\/(.*?)["']/g;
  let m;
  while ((m = re.exec(html)) !== null) {
    // Normalise double slashes produced by Hugo templates
    const p = m[1].replace(/^\/+/, "");
    // Skip fragment-only links (#section), empty paths, and external links
    if (!p || p.startsWith("#")) continue;
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

  // Modern font
  assert(html.includes("Inter"), "uses Inter font");
  assert(!html.includes("Kaushan"), "no longer uses Kaushan Script font");

  // GA4 only
  assert(html.includes("G-XXH6Y7X45B"), "includes GA4 tag");
  assert(!html.includes("UA-93253018-1"), "removed legacy Universal Analytics");

  // No IE8 shims
  assert(!html.includes("html5shiv"), "removed IE8 html5shiv");
  assert(!html.includes("respond.js"), "removed IE8 respond.js");

  // Empty sections removed
  assert(!html.includes('id="portfolio"'), "removed empty portfolio/Believe section");
  assert(!html.includes("sponsor-1"), "removed empty sponsors section");

  // Timeline updated
  assert(html.includes("2019-2023"), "timeline includes Meta years (2019-2023)");
  assert(html.includes("2023-Present"), "timeline includes Pure Storage (2023-Present)");
  assert(html.includes("Pure Storage"), "mentions Pure Storage");

  // JS includes point to versioned paths
  assert(html.includes("js/jquery-v3.3.1/jquery.min.js"), "jQuery uses versioned path");
  assert(
    html.includes("js/bootstrap-v3.3.7/bootstrap.min.js"),
    "Bootstrap JS uses versioned path"
  );
  assert(html.includes("js/agency.js"), "includes agency.js");

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

  // Fixed subtitle
  assert(!html.includes("Blog Description"), 'no placeholder "Blog Description" subtitle');
  assert(
    html.includes("Thoughts on software engineering"),
    "has real blog subtitle"
  );

  // Placeholder posts removed
  assert(!html.includes("Second post"), "removed placeholder post-02");
  assert(!html.includes("Third post"), "removed placeholder post-03");
  assert(!html.includes(">Posts<"), "removed Posts index entry");

  // Real post kept
  assert(
    html.includes("Building a theme with Hugo"),
    "kept real blog post (post-01)"
  );

  // Fixed asset paths
  assert(
    html.includes("css/bootstrap-v3.3.7/bootstrap.min.css"),
    "CSS uses versioned bootstrap path"
  );
  assert(
    html.includes("js/jquery-v3.3.1/jquery.min.js"),
    "JS uses versioned jQuery path"
  );

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");

  // Has social links in footer
  assert(html.includes("fa-linkedin"), "footer has LinkedIn icon");
  assert(html.includes("fa-github"), "footer has GitHub icon");

  // No old analytics
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");
}

// ===================================================================
console.log("\n=== About (about/index.html) ===");
// ===================================================================
{
  const html = readFile("about/index.html");

  // No Lorem Ipsum
  assert(!html.includes("Lorem ipsum"), "no Lorem Ipsum placeholder text");

  // Has real content
  assert(
    html.includes("Marco Montalto Monella"),
    "mentions name in bio"
  );
  assert(html.includes("Pure Storage"), "mentions current employer");
  assert(html.includes("Meta"), "mentions former employer");
  assert(html.includes("NYU"), "mentions education");

  // Fixed asset paths
  assert(
    html.includes("css/bootstrap-v3.3.7/bootstrap.min.css"),
    "CSS uses versioned bootstrap path"
  );

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");
}

// ===================================================================
console.log("\n=== Contact (contact/index.html) ===");
// ===================================================================
{
  const html = readFile("contact/index.html");

  // Fixed asset paths
  assert(
    html.includes("css/bootstrap-v3.3.7/bootstrap.min.css"),
    "CSS uses versioned bootstrap path"
  );
  assert(
    html.includes("js/jquery-v3.3.1/jquery.min.js"),
    "JS uses versioned jQuery path"
  );

  // Has contact form
  assert(html.includes('id="contactForm"'), "has contact form");

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");

  // No old analytics
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");
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
  assert(!html.includes('id="portfolio"'), "no Believe nav link");
}

// ===================================================================
console.log("\n=== Blog Post (post/post-01/index.html) ===");
// ===================================================================
{
  const html = readFile("post/post-01/index.html");

  // Fixed asset paths
  assert(
    html.includes("css/bootstrap-v3.3.7/bootstrap.min.css"),
    "CSS uses versioned bootstrap path"
  );
  assert(
    html.includes("js/jquery-v3.3.1/jquery.min.js"),
    "JS uses versioned jQuery path"
  );

  // Has Home nav link
  assert(html.includes(">Home<"), "has Home navigation link");

  // Has social links in footer
  assert(html.includes("fa-linkedin"), "footer has LinkedIn icon");
  assert(html.includes("fa-github"), "footer has GitHub icon");

  // No old analytics
  assert(!html.includes("UA-93253018-1"), "no legacy Universal Analytics");

  // Has GA4
  assert(html.includes("G-XXH6Y7X45B"), "has GA4 tag");
}

// ===================================================================
console.log("\n=== CSS Modernization (css/agency.css) ===");
// ===================================================================
{
  const css = readFile("css/agency.css");

  // New color palette
  assert(css.includes("#0d9488"), "uses teal primary color (#0d9488)");
  assert(css.includes("#1e293b"), "uses dark slate (#1e293b)");
  assert(css.includes("#5eead4"), "uses mint accent (#5eead4)");

  // Old Facebook blue gone
  assert(!css.includes("#3b5998"), "removed Facebook blue (#3b5998)");

  // Modern font
  assert(css.includes('"Inter"'), "uses Inter font family");
  assert(!css.includes("Kaushan"), "removed Kaushan Script");

  // Modern features
  assert(css.includes("gradient"), "uses CSS gradients");
  assert(css.includes("box-shadow"), "uses box shadows");
  assert(css.includes("translateY"), "uses transform for hover effects");
}

// ===================================================================
// Summary
// ===================================================================
console.log(`\n${"=".repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log(`${"=".repeat(50)}\n`);

process.exit(failed > 0 ? 1 : 0);
