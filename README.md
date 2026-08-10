# Maison Amira — Website

A fine-patisserie showcase site for **Maison Amira**, Sweifieh, Amman.
Hand-built, self-contained **HTML + CSS + vanilla JS** — no framework, no build step.

> _"A love letter, written in sugar & rose."_

---

## Quick start

**Just open it.** Double-click `index.html`, or drag it into a browser.

To preview with a local server (recommended so the map + fonts behave exactly as in production):

```bash
# from this folder
python -m http.server 8000
# then visit http://localhost:8000
```

**To publish:** upload the whole folder to any static host — Netlify, Vercel, Cloudflare Pages, GitHub Pages, or plain shared hosting. Drag-and-drop the folder onto Netlify and you're live. No configuration required.

---

## What's inside

```
maison-amira/
├── index.html          ← page content & structure
├── css/styles.css      ← all styling, layout, animations
├── js/main.js          ← loader, scroll reveals, parallax, nav, lightbox, mobile menu
├── assets/img/         ← 11 photographs (locally hosted, optimised)
└── README.md
```

Everything is self-contained. The only external calls are **Google Fonts** and the
**Google Maps** embed — both degrade gracefully offline.

---

## Design system

| | |
|---|---|
| **Style** | Blush & Gold Patisserie — soft, romantic, "quietly high-end" |
| **Display font** | Cormorant Garamond |
| **Body font** | Montserrat |
| **Arabic accent** | Amiri (ميزون أميرة) |
| **Cream** | `#FCF8F3` |
| **Blush / rose** | `#F4DEE2` · `#C5859A` |
| **Antique gold** | `#B08C4A` (foil gradient for accents) |
| **Ink (text)** | `#4A2A31` |

All colours are CSS variables at the top of `css/styles.css` (`:root`) — change them in one place.

---

## Customising it

Everything below is plain text you can edit directly.

### 1. Contact details  (search `index.html` for these)
- **Phone / WhatsApp** — placeholder `+962 7 9000 0000`. Replace the display number and
  the `wa.me/962790000000` / `tel:+962790000000` links (they appear in the Visit section and footer).
- **Instagram** — placeholder `@maisonamira` → `instagram.com/maisonamira`.
- **Address & hours** — in the `VISIT` section.
- **Map** — the `<iframe>` in the Visit section points at Sweifieh. Replace the `src` with your
  exact Google Maps "Embed a map" link once you have the precise pin.

### 2. Menu items & prices
In the `MENU` section: three featured cards (`.feat`) plus two price lists
(`La Table Française` / `La Table Levantine`). Prices are in Jordanian Dinar. Edit freely.

### 3. Photographs
Swap any file in `assets/img/` — keep the **same filename** and it just works.
Recommended: JPG, ~1000–1600px wide, saved at ~80% quality.

| File | Used for |
|------|----------|
| `hero.jpg` | Hero background (also the social-share image) |
| `story.jpg` | Our Story portrait |
| `macaron.jpg` · `kunafa.jpg` · `millefeuille.jpg` | Featured trio |
| `display.jpg` · `box.jpg` · `eclair.jpg` · `basbousa.jpg` · `cake.jpg` · `tart.jpg` | Gallery |

Every image sits on a blush-gold gradient placeholder, so nothing looks broken while photos load.

### 4. Optional: a real video hero
The hero currently uses the still image with a slow "Ken Burns" zoom. To use a muted video instead,
drop `assets/hero.mp4` (and optionally `assets/hero.webm`) and **uncomment** the `<video>` block in the
hero section of `index.html`. It layers over the poster with no other changes. Keep videos short,
muted, and compressed (< ~4 MB) so mobile stays fast.

---

## Animations & interactions

Elegant and GPU-friendly — an animated logo intro, a choreographed hero entrance
(line-by-line headline reveal + gold shimmer), scroll-reveals, hero parallax, a menu
marquee, image hovers, a condensing sticky nav, and a lightbox gallery.

**Custom cursor** (desktop / fine-pointer only): a gold dot + trailing ring that adapts
per section — lighter gold over the dark sections (hero, marquee, footer), antique gold
over the light ones. It swells over links/buttons, becomes a "View" disc over gallery
images, magnetically pulls buttons and social icons, and tilts the menu cards, gallery
tiles, and story image subtly toward the pointer.

- **Fully responsive** — verified at 375px, tablet, and desktop; no horizontal scroll.
- **Respects `prefers-reduced-motion`** — animations reduced/disabled, and the custom
  cursor is switched off entirely (native cursor stays).
- **Touch-safe** — the custom cursor never activates on touch / coarse-pointer devices.
- **Fails safe** — content is always visible even if JavaScript doesn't load.

---

## Notes

- Asset links use `?v=1` for cache-busting. When you replace a CSS/JS file, bump it to `?v=2`
  so browsers fetch the new version.
- The SVG monogram logo is drawn in-page (in `index.html` / styled in `styles.css`) — no image file.
- Fonts: Google Fonts (open licence). Photography: generated for this project.
- English-only by design. The markup is structured so an Arabic/RTL version could be added later.
