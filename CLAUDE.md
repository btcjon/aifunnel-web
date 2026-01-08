# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

aiFunnel is a static landing page for an AI automation service, deployed to Netlify at https://aifunnel.chat.

## Architecture

This is a simple static site with no build process:
- `index.html` / `aifunnel.html` - Main landing pages (identical content)
- `images/` - Logo assets (SVG, JPEG)
- `og-image.jpg` - Open Graph social sharing image

The pages are self-contained single-file HTML with inline CSS and JavaScript featuring:
- Custom cursor system with trails
- Particle system with physics (canvas-based)
- Web Audio API sound effects
- Parallax floating orbs
- Modal contact form

## Deployment

Deploy to production via Netlify CLI:
```bash
netlify deploy --prod
```

Site ID is stored in `.netlify/state.json`. No build step required - deploys the directory as-is.

## Design Philosophy

Follow the "Digital Luminescence" aesthetic documented in `design-philosophy.md`:
- Deep black backgrounds (#000000, #050508)
- Electric cyan (#00f5ff) and purple (#8b5cf6) accents
- Orbitron font for headlines, JetBrains Mono for body
- Glow effects, scan lines, and atmospheric depth
- Minimal text - let visuals communicate

## Issue Tracking

Uses `bd` (beads) for work tracking. See AGENTS.md for workflow.
