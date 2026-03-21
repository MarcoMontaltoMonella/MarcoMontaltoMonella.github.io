---
title: How Claude Rebuilt This Website
description: The story of how I teamed up with an AI assistant to redesign and modernize my personal website from scratch.
date: 2026-03-21
---

If you're reading this, you're looking at a website that was almost entirely rebuilt by [Claude](https://claude.ai), Anthropic's AI assistant. And honestly? It was one of the most interesting side projects I've done in a while.

## The backstory

My personal website had been running on [Hugo](https://gohugo.io/) for years. It was built with the Bootstrap 3 "Agency" and "Clean Blog" themes — functional, but showing its age. The styling had that unmistakable 2015 vibe: heavy shadows, rigid grids, and a design language that felt more like a startup landing page template than a personal site.

I'd been meaning to modernize it for a while, but between work and life, it kept falling to the bottom of the to-do list. Then I thought — why not see what Claude can do with it?

## What changed

Pretty much everything:

- **Dropped Bootstrap 3** — replaced with modern CSS using custom properties, CSS Grid, and Flexbox. No framework dependency needed in 2026.
- **Dropped jQuery** — vanilla JavaScript handles everything: smooth scrolling, mobile menu, scroll animations, and form submission.
- **Fixed all the broken paths** — the old site used absolute URLs (`https://mmmarco.com/...`) everywhere, which meant nothing worked when previewing locally.
- **Unified the design** — the homepage and blog pages used to be two completely different templates. Now everything shares one clean stylesheet.
- **Removed Hugo artifacts** — categories, tags, pagination directories, XML feeds... all the generated cruft from a static site generator I was no longer using.
- **Created a simple blog build system** — instead of Hugo's complexity, a single Python script converts Markdown files into blog posts. Write a `.md` file, run the script, done.

## The design

The new look is clean and minimal: a teal-and-slate color palette, the Inter typeface, generous whitespace, and subtle animations that respect the `prefers-reduced-motion` setting. The hero sections use gradient overlays on photos, cards have gentle hover effects, and the timeline on the homepage actually looks like it belongs in this decade.

## What I learned

Working with Claude on this was surprisingly collaborative. I'd describe what I wanted — "fix the broken styling and pick a fresh modern look" — and it would make decisions about color palettes, layout systems, and code architecture. When something wasn't right, I'd course-correct, and it would adapt.

The whole process felt less like using a tool and more like pair-programming with someone who has very strong opinions about CSS custom properties.

## What's next

This blog now runs on the simplest possible setup: Markdown files in a `_posts/` folder, a Python build script, and static HTML served by GitHub Pages. No build tools, no npm dependencies, no config files. If I want to write a new post, I create a Markdown file and run `python3 build.py`.

Sometimes the best stack is the one with the fewest moving parts.
