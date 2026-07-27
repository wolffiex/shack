# Animation internals

## The rays clock is drawn by its own rays

`rays2.py` never draws the digits into the output. `time_image` accumulates color
*only where a ray has crossed a glyph pixel*, then decays 4% per frame — roughly a
2.5s phosphor trail. The final frame is `screen(rays, time_image)`.

Consequences:

- **A single frame is not evidence.** Stills show broken, gappy digits; the clock is
  legible because the eye integrates ~25 frames. Do not judge legibility, contrast, or
  "noise" from extracted frames. Rays crossing the digits are not interference, they
  are the render mechanism.
- Ray density is highest at the origin and falls off with distance, so the origin
  doubles as the illumination hot-spot.

## Layout invariants (`get_time_pixels`)

- The colon is **pinned to panel center**; hours are right-justified against it and
  minutes left-justified after it. Centering the whole string instead slides the colon
  ~8px when the hour drops to one digit (`%-I`), dragging the ray origin with it.
- The **upper colon block is never drawn**. It is the ray origin; converging rays
  render it. Only the lower block is a lit pixel.
- `COLON_GAP` blank columns on both sides, solved from **measured ink**, not metrics.
  `font.getbbox()` / `getlength()` return the *advance* box including side bearings —
  for this font `getbbox("10") == (0,0,23,12)`, identical to `getlength`. Aligning to
  it misplaces digits. `ink_bounds()` uses the glyph mask's bbox, which is the ink.
- Known trade-off: pinning the colon leaves single-digit hours right-weighted — block
  center lands ~6px right of panel center for `9:45`. Accepted for origin stability.

## Verifying visually

Do not eyeball spacing from rendered animations; the phosphor bloom hides the geometry.
Measure the raw lit-pixel map from `get_time_pixels()` instead — magnified, on a pixel
grid, counting the blank columns either side of the colon. Judging motion is the other
way round: only a played-back animation shows whether the clock reads.

## Timing

15s animations, 10fps (`FRAME_TIME` 100ms) = 150 frames, generated in 90s segments and
sliced at 12s steps so each animation overlaps the next. `clock_rays()` and
`clock_radar()` are generators: `next()` once to prime, then `send(t)` per frame.
