# Flat 3D sections plan

The flat version of the Catalyst walk-through: every stop is a normal full-screen
section of the page, one below the other, each with its own live 3D scene behind its
text. Made on 2026-10-05 as a full, independent copy of the walk-through project
(`catalyst-hero`, repo https://github.com/pedram-kh/walk-through); nothing is shared
between the two folders.
Repo: https://github.com/pedram-kh/walk-through-3D

## What differs from the walk-through (decided 2026-10-05)

- Sections stack like a normal web page, each exactly one screen tall. No spacers,
  no hold zones, no scroll braking, no camera journeys (curl, tilt, travel).
- No freeze and no black and white: every stop is always in colour. A stop animates,
  plays its videos and reacts to the cursor while any part of its section is on screen,
  and stops when it scrolls off.
- No particles anywhere: no dust, no stop currents, no journey currents.
- Each stop draws on its own canvas inside its section, so the 3D scrolls exactly with
  the section's text (a shared fixed canvas would trail native scrolling by a frame).
- Loading: stop 01 first; then, while the visitor views stop N, stops N+1 and N+2 load
  in the background (and N-1 for a visitor landing further down), one at a time. Nothing
  is unloaded. A section shows its poster until its stop is ready.
- Progress dots on the left are plain jump links (smooth scroll to the section).
- Posters re-rendered without particles from each stop's `.blend`
  (`tools/render_poster.py`); the scenes themselves were not rebuilt.

## How each new stop is built

1. You provide reference images. I ask the questions under "Content and
   buttons" and wait for your answers.
2. Blender graybox: a Python script places simple shapes and sets the stop's rest
   camera. Render a preview and wait for approval of the composition.
3. Blender detail: real geometry and materials, still from a script.
4. Export this stop as its own files, add it to `stops.json`, add its section to
   `index.html`.
5. Add the behaviour, text and buttons exactly as answered.
6. Check it, record the numbers here, commit, and report. Then wait.

Nothing is built, changed or pushed for a new stop without your confirmation.

## Content and buttons: ask, do not assume

Before building any stop, ask these and wait for the answers:

1. Text: what text appears at this stop, and for each piece, is it HTML over
   the scene or part of the 3D model?
2. Buttons: which buttons does this stop have, what does each one do when
   clicked, and is each one a 3D object or an HTML button?
3. Button behaviour: how should each button look at rest, on hover and on click?
4. Scene behaviour: what moves when idle, what reacts to the cursor, and what
   happens on click or drag.
5. Media: which images or videos belong to this stop, and where they sit.

Do not choose any of these myself. If an answer leaves something open, ask
again. If a choice will hurt performance, keyboard access or the poster page,
say so in one line and let you decide. Record the answers in that stop's
`stop.json` before building.

## Stops

| Stop | Section | Notes |
|---|---|---|
| 01 | Hero | Tile wall, three videos, captions. |
| 02 | Creative for (client logos) | Logo grid with hover. |
| 03 | 02 The problem | Drifting card rows with motion trails. |
| 04 | 13 Creative cycle | Ring, stages, signal, mark; rows drive the signal. |

The `brief` in each `stop.json` is the record of what was agreed for the walk-through;
its notes on the current, freezing and black and white no longer apply here.

## Architecture

### Folder layout

```
index.html              the page: fixed nav, one full-screen section per stop
style.css               page and section styles (html.live = live 3D, section.scene-ready = its stop is drawn)
app.js                  live 3D or posters only (touch, reduced motion, data saver, failure)
stops.json              stops in order: folder, section id, frame (origin, rotation), rest camera, poster
assets/                 page-level files (logo)
runtime/
  runtime.js            per-section canvas, renderer and camera, sizing, pointer, frame loop, quality guard
  loader.js             loads the stop on screen and the two after it, one at a time
  dots.js               progress dots on the left: jump links
  materials.js          shared helpers used by the stop shaders (the grey uniform stays at 0 here)
stops/
  01-hero/              build.py, stop.js, stop.json, stop.glb, stop.blend, poster.jpg, media/
  02-clients/           build.py, stop.js, stop.json, stop.glb, stop.blend, poster.jpg, fonts/
  03-problem/           atlas.py, build.py, stop.js, stop.json, stop.glb, stop.blend, poster.jpg, cards.jpg/json
  04-cycle/             build.py, stop.js, stop.json, stop.glb, stop.blend, poster.jpg, core.svg
tools/
  render_poster.py      Blender: remove particle objects from a stop's .blend, save it, render poster.jpg
vendor/three/           unchanged
```

Stop module interface (`stops/NN-name/stop.js`): `load(ctx)` returns
`{ group, setFrozen(bool), setGrey(0..1), setVisible(bool), resize(size), update(dt), dispose() }`.
`ctx` gives the stop its folder, its section, its camera (at the rest view), an overlay
element inside the section for HTML captions, the pointer (-1..1 in the section's own
view, `inside` while over the section) and `invalidate()`. The runtime only uses
`setFrozen` (false while on screen), `resize` and `update`.

## Rule 1: performance

- Test device: this Mac, Intel Iris Plus Graphics, 1920 x 1080. It must hold
  30 fps or better while scrolling through the page.
- Only stops whose sections are on screen animate, render and play video; while
  scrolling from one section to the next, at most two do.
- Per stop: at most 60,000 triangles, 40 draw calls and one playing video.
  Pixel ratio capped at 1.5 (drops to 1 if the frame rate stays under 24).
  Agreed exception: stop 01 plays three videos.
- `document.documentElement.pageDiagnostics` in the console: fps, live and loaded
  stops, draw calls, pixel ratio.

## Rule 2: loading

- Stop 01 loads first and shows as soon as it is ready. Nothing else blocks it.
- Then stops N+1 and N+2 load in the background while the visitor views stop N.
- Each section shows its poster until its stop is ready. Keep each stop under 2 MB
  excluding video (stop 01 is the agreed exception).

## Fallback

- The page is real HTML in normal flow: search engines, keyboards and screen readers
  read it as is.
- Touch devices, reduced motion, data saver and any graphics failure get the sections
  with their posters (and the brand list as text at stop 02).

## Machine

- Blender 4.5.14 LTS on an Intel Mac, run in the background:
  `/Applications/Blender.app/Contents/MacOS/Blender --background --python <script>`
- Render with Cycles on CPU, low samples. Scripts must be deterministic.
- Serve with: `python3 -m http.server 4176` (4175 is the walk-through).

## Log

Rows before 2026-10-05 "Flat version created" are the walk-through's history, kept for reference.

| Date | Stop | Event | Rest fps | Travel fps | Size (excl. video) |
|---|---|---|---|---|---|
| 2026-10-03 | 01 | Hero approved as a scene; first commit pushed | not measured | n/a | 6.1 MB |
| 2026-10-03 | 01 | Exceptions agreed: three videos, size above 2 MB | | | |
| 2026-10-03 | 01 to 02 | Route skeleton: hero as stop 01, placeholder stop 02, curtain, freeze and grey, curl and 90-degree tilt down, travel, dots, flat fallback | not measured (run ?bench) | not measured | 01: 6.1 MB, 02: 0.1 MB |
| 2026-10-03 | 01 to 02 | Transition move: half circle (radius 8) swinging toward the objects while tilting 90 degrees, then travel 14; clearance check in build_route.py (closest pass 4.4 units) | not measured | not measured | |
| 2026-10-03 | 01 to 02 | Tilt 60 degrees, travel 8; current continues through the journey (stop 01 tail rerouted, currents/t01.bin, 10,441 particles); ~56k points on screen during the journey | not measured (run ?bench) | not measured | journey current 0.45 MB |
| 2026-10-03 | 01 to 02 | Frame rate judged OK by eye on the test Mac; no ?bench numbers yet | OK (by eye) | OK (by eye) | |
| 2026-10-04 | 02 | Brief recorded in stop.json; graybox approved (5 x 2 grid at varied depths, current threads the middle line and leaves left, journey current hands over to it) | not measured | not measured | 0.7 MB (graybox) |
| 2026-10-04 | 02 | Detail + behaviour built: wordmarks in their real fonts, grid merged to 3 draw calls (5 for the stop, 15.5k triangles), hover like catalyst-growth.com (lift, corner glow, rotating gradient border, wordmark brighten/dim), dust and current part around the cursor; flat page shows the brands as a list. Awaiting approval | not measured (preview pane) | not measured | 1.59 MB (+ journey current 0.49 MB) |
| 2026-10-04 | 02 | Dust removed at your request: the current is the only particles at stop 02 | 60 (preview, at rest) | not measured | 1.51 MB |
| 2026-10-04 | 01 to 02 | Smoother, shorter scrolling: camera glides after the scroll (0.12 s), journeys 3 -> 2 screens (page 5 -> 4 screens so far), camera path 120 -> 240 samples | not measured | not measured | |
| 2026-10-04 | 02 | Stop 02 approved (hover matched to the live site, hovered cell drawn in front, lift 0.4) | 60 (preview) | not measured | 1.51 MB |
| 2026-10-04 | 03 | Brief recorded in stop.json; graybox approved: three rows of 5 upright cards turned 25 degrees in a checkerboard zigzag (toward / away from the screen), all text in HTML around them and the whole section in one viewport; current enters from the right, goes around the cards in two strands and leaves through the top-right; turn left 60 degrees from stop 02. Journey currents now stay out of the next stop's arrival view when its current starts off screen | not measured | not measured | 0.85 MB (graybox, + journey current 0.52 MB) |
| 2026-10-04 | 03 | Detail + behaviour built: card faces from the catalyst-growth.com photos (stop 01 set) with the landing's hairline border and label chip in one texture (cards.jpg, atlas.py); 6 cards per row in the drift loop (5 on screen), drifting like the landing (rows 1 and 3 right, row 2 left), fading per pixel at the row ends and wrapping off screen so the checkerboard holds; hero-style tilt and lift near the cursor; the landing's violet-to-blue motion trail behind each row; colour when live. 5 draw calls for the stop. Awaiting approval | not measured (preview pane) | not measured | 1.3 MB (+ journey current 0.52 MB) |
| 2026-10-04 | 03 | Stop 03 approved ('02 — The problem' label removed at your request) | not measured | not measured | 1.3 MB |
| 2026-10-04 | 04 | Brief recorded in stop.json (landing section 13, Creative cycle, as stop 04; sections 03-12 skipped for now). Graybox built: ring on the left with stage spheres, signal, trail and the extruded Catalyst mark; title, rows and stage labels in HTML; current from below, around the ring, out to the left; turn up 60 degrees from stop 03 (closest pass 4.7 units). Graybox approved | not measured | not measured | |
| 2026-10-04 | 04 | Detail + behaviour built: ring, trail (the landing's conic violet-blue-teal), stage spheres with rim and centre colours and glows, signal, halo and core glow drawn in the browser from stop.json; the extruded mark from stop.glb (36 KB). Signal runs at the landing's timing (1.8 s per stage, eased settle); the reached stage lights in its colour, with its row and label; hover, focus or click on a row moves the signal there and holds it. Mark tilts and lifts a little near the cursor. Runtime: stops now get their section element in ctx. 11 draw calls for the stop. Awaiting approval | not measured | not measured | 0.6 MB (+ journey current 0.5 MB) |
| 2026-10-04 | 04 | Changes at your request: the ring turns on its vertical axis (one turn in 30 s); the stage labels are 3D (canvas text in the page's mono font, following their spheres and facing the camera); the list's lines and the active underline are 3D, measured from the HTML rows, so only the text leaves with the curtain. 13 draw calls. Awaiting approval | not measured | not measured | 0.6 MB |
| 2026-10-05 | 04 | Stop 04 approved | not measured | not measured | 0.6 MB |
| 2026-10-05 | 01 | Dust removed at your request: stop.js no longer loads or draws dust.bin, so the current is the only particles at the hero (the build and the poster still include the dust; rebuilding stop 01 would reshuffle its approved current). Approved | not measured | not measured | 0.59 MB less to download (dust.bin no longer fetched) |
| 2026-10-05 | 01 | Removed at your request: the 'Strategy / Production / Performance / Scale' list and the thin vertical background lines (HTML and CSS). Approved | not measured | not measured | |
| 2026-10-05 | all | Currents 40% less dense at your request: runtime/flow.js draws a fixed, even 60% of every current's particles (CURRENT_DENSITY 0.6), stops and journeys alike; paths unchanged, no rebuilds. Points on screen at the hero 45,013 -> 27,045. Approved | not measured | not measured | |
| 2026-10-05 | 01 | Mono tiles restyled at your request, after catalyst-growth.com's photos: soft muted black and white (cool blue-grey lights, deep blacks) under a halftone screen, teal / violet fringes where shadow meets light, faint coloured grain in the blacks. Halftone anti-aliased and faded where it would cause moire; grain in screen pixels. The 8 colour tiles are unchanged; the poster still shows the old look. Approved | not measured | not measured | |
| 2026-10-05 | all | Hold zones at your request: each section is wrapped in a hold element half a screen taller than the screen (section sticky inside), so every stop stays live and in colour for an extra half screen of scrolling; the stop's dot becomes a pill that fills violet -> teal through it, then the curtain and journey start. Colour starts fading in over the last 20% of a journey into a stop (direction-aware). Inside a hold zone, wheel / trackpad scrolling is braked (x0.55, max 8% of a screen per event; touch left native). Scroll snapping removed (it would pull the page back out of a hold zone). Dots fly to the start of a hold zone. Page 12 screens for 4 stops (was 10). Then: the pill is black, filling white (not the gradient), and no single wheel step can carry the page into a zone past its edge, so every arrival from above starts with an empty pill. Approved | not measured | not measured | |
| 2026-10-05 | all | Pause motion button removed at your request (visitors with reduced motion set still get the flat page). Approved | not measured | not measured | |
| 2026-10-05 | all | Flat version created at your request (copy of the walk-through at commit 0f369d7): sections stacked one screen each, no journeys, freeze, black and white or hold zones; all particles removed (stop.js, build.py, stop.json; flow.bin, dust.bin, currents/, route.json, build_route.py, flow_common.py, flow.js, route.js, bench.js deleted); one canvas per section; stop N+1 and N+2 preloaded; dots as jump links; posters re-rendered without particles. Awaiting approval | not measured | not measured | |
