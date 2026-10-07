# Cimidona Forte — 4 motion-graphic ads (Arabic, 9:16)

Four vertical (1080×1920, 30 fps) social ads for **Cimidona Forte** (Labatec, distributed in KSA by MediSense),
voiced in Saudi-dialect Arabic with word-synced captions. Styles mirror the four reference videos.

| # | Concept | Style | Length |
|---|---------|-------|--------|
| v1 | «٣ أسباب تخلّيكم تجرّبون سيميدونا فورت» | Dark neon listicle (01/02/03 progress bars, rings, glow) | ~36 s |
| v2 | Symptoms → solution | Light illustrated, karaoke captions with green word highlights | ~42 s |
| v3 | «قبل زواج بنتي بشهرين…» | Cinematic AI-photo story, chapter titles, wedding countdown card | ~44 s |
| v4 | «سنة الخمسين…» first-person testimonial | Cool-toned AI-photo story, pharmacist advice, daily calendar card | ~44 s |

All four end on the HealthStore.sa CTA («اطلبيه الحين من هيلث ستور» / «تلقينه في هيلث ستور») plus a disclaimer.

## Product facts used (source: medi-sense.com/product/cimidona-forte)
- Standardised *Cimicifuga racemosa* (black cohosh) root extract — **non-hormonal**
- For menopausal symptoms: hot flushes, night sweats, mood changes, sleep issues
- One tablet daily; many women report improvement within 2–4 weeks
- 30 tablets · HealthStore.sa (SAR 98)
- Not for pregnancy, breastfeeding or active liver disease; consult a doctor if on hormonal therapy

## Pipeline
1. `scripts.json` — VO lines, highlight words, per-video timeline (gaps, SFX cues, music style).
2. Voiceover — Higgsfield `seed_audio`, custom voice element **"Cimidona narrator"**, one clip per line
   (URLs in `jobs.json`). Lines were QA'd with faster-whisper (medium); five re-takes replaced takes
   that dropped or added words.
3. Story stills (v3/v4) — Higgsfield Nano Banana Pro with a character portrait + the real product photo as references.
4. `render/build_audio.py` — trims clips, applies 1.1× tempo, aligns word timings (whisper),
   lays out the timeline, synthesises a music bed + whooshes/chime, ducks music under VO, loudness-normalises (−15 LUFS).
5. `render/v1.html`, `v2.html`, `v3.html`/`v4.html` (+ `story.js`/`story.css`) — deterministic HTML compositions
   driven by `window.seek(t)` (`render/lib.js`).
6. `render/render.mjs` — Playwright captures every frame → ffmpeg (H.264 CRF 18) → muxed with AAC audio.
7. `render/run.sh <v1..v4> [full|stills auto:N] [upload_url]` — runs the whole thing inside the Higgsfield sandbox.

To change copy: edit `scripts.json`, regenerate the affected TTS line(s), update `jobs.json`, re-run `run.sh` with `REBUILD_AUDIO=1`.
