# Request flow

## The serve/generate loop

The device (and the simulator) polls `v1/preview.webp` about every 12s. Generation is
*pulled* by that traffic, not scheduled:

1. `get_preview` picks an animation, stamps `served_at`, and redirects to its file.
   With an empty DB it saves a **blank `Animation()` and still stamps `served_at`** —
   that is what bootstraps a cold start, so no seeding is needed.
2. `generate` refuses to do anything unless `is_running()` — an animation served within
   the last minute. No traffic, no generation.
3. `get_segment_start` skips generation when ~90s of future coverage already exists.

If animations look stale after a code change, the queue is the reason: up to 90s of
already-rendered frames are waiting. Clear it rather than waiting.

## Clock style selection

`?source=rays|radar` on `command/generate` pins the style instead of choosing randomly.
It only affects styles *chosen from now on* — generation stays non-destructive, so with
a full buffer the coverage check returns `Already have clock` and the pick appears to do
nothing for up to 90s. Clearing the queue is the separate, POST-only `clear-queue`
action; keeping it separate is deliberate, since `command/generate` is a GET the device
polls and must not delete state. Unrecognized values are logged and ignored, not
rejected; this is a background command.

Note `simulator.js` fires an *unpinned* `generate()` one second after page load, which
can roll the other style before you touch the form.

## Simulator controls

Server-rendered plain forms, no client state. The style `<select>` is a GET form whose
selection lives in the query string and is read back by `get_simulator`; JS reads it
from `document.body.dataset.clockSource`. `Clear queue` is a POST to
`command/clear-queue` that drops unserved animations and redirects back, preserving the
selection. Served animations are left alone — history, not queue.

## Endpoints

| path | purpose |
|---|---|
| `v1/preview.webp` | serves the next animation; stamps `served_at` |
| `command/generate` | generation tick; accepts `?source=` |
| `command/clear-queue` | POST; drops unserved queued animations |
| `command/cleanup` | deletes render files and rows older than 4h |
| `simulator` | dev UI mimicking the device poll loop |
