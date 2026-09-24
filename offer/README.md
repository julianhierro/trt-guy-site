# TRT Guy offer page — trt-guy.com/offer/

Low-ticket sales page in the same format as the Jacked Vegans 7-Day Challenge page.
Every slot is a [bracketed placeholder] saying what goes there; swap in the real copy in the editor.

- Edit: https://trt-guy.com/offer/?edit=1 (dashboard password)
- Editor store: site `trtguy-offer`, page 1, on jv-dashboard /api/content
- Local editor.js = the site editor plus: double-click image → replace, double-click video → swap,
  all `.cta` buttons / `.price-note` lines kept identical (text + link).
- After publishing: `python3 ../scripts/bake-edits.py offer/index.html trtguy-offer` (from repo root), then push.
- `build.py` re-stamps element ids from src/ — only for structural changes, never after edits are published.
- Has `noindex` until it is launched; remove the robots meta in src/head.html then.
