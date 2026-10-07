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

## Pipeline (current — no Higgsfield, see CLAUDE.md)
1. `scripts.json` — VO lines, highlight words, per-video voice/persona and timeline.
2. `render/tts_gemini.py` — Google AI Studio TTS (`gemini-3.1-flash-tts-preview`), Saudi (Riyadh/Najdi) dialect.
   One whole-script request per video (voices: Leda for v1/v2, Vindemiatrix for v3/v4), split into lines by an
   alignment step, then checked by a Gemini model for dialect and word-for-word accuracy (`audio/qa_report.json`).
   Auth: `GEMINI_API_KEY` (sent as `?key=`). Free tier allows ~10 TTS requests/day per model.
3. `render/build_audio.py` — timeline, word timings, synthesized music bed; no transition sounds, soft end chime only.
4. `render/render_local.sh <v1..v4>` — fetches the original images/cut-outs, renders frames with Playwright, muxes to `out/`.
