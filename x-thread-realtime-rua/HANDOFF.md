# Handoff: realtime-rua launch videos

This folder is the launch kit for the blog post "Getting Robot-Use Agents to Run in Real Time"
(`content/blogs/realtime-rua/`): the X thread draft, its media, every script that makes the media, and all the
inputs those scripts need. If you are an agent, read this file first, then `src/README.md` for the details of each
script.

It lives on branch `blog/realtime-rua` of `shaoxiongduan/hao-ai-lab.github.io`, a public fork of the lab site, so
everything pushed here is public. This folder will be removed or moved to its own branch before the blog's pull
request to `hao-ai-lab/hao-ai-lab.github.io`. Ask Shaoxiong Duan before changing that plan, posting anything, or
opening a pull request.

## What makes what

```
assets/opening + assets/runs ──> src/main-video ──────────────> 01-main-video.mp4
assets/cameras + assets/timeline-clips + assets/fonts
                ──> src/timeline-clips ──> blog Videos 1-3 ──> src/clips ──> 05-cup-game-3.5x.mp4
                    (render.py)            (content/blogs/                   06-crumpled-towel-8x.mp4
                                            realtime-rua/img/)
blog page (hugo server) ──> src/figures ──────────────────────> 02-, 03-, 04-*.png
thread.md + media ──> src/thread-page ────────────────────────> thread preview page
blog page (hugo server) ──> src/blog-preview ─────────────────> blog preview page
```

| Output | Script | Look is set in | Inputs |
|---|---|---|---|
| `01-main-video.mp4` (41.6 s, 1920x1080) | `src/main-video/make.sh` | `main-video.html` (HTML/CSS/JS, one frame per `render(t)`) | `assets/opening/`, `assets/runs/` |
| Blog Videos 1-3, `content/blogs/realtime-rua/img/<run>-timeline-<speed>x.mp4` (1280x720) | `src/timeline-clips/make.sh` | `render.py` (Pillow drawing) | `assets/cameras/`, `assets/timeline-clips/`, `assets/fonts/` |
| `05-cup-game-3.5x.mp4`, `06-crumpled-towel-8x.mp4` | `src/clips/make.sh` | the blog videos, plus text overlays from `overlay.html` | blog Videos 1 and 3 |
| `02-benchmark-vs-real-robot.png`, `03-merged-round-trips.png`, `04-pipelining.png` | `src/figures/make.sh` | the blog's figures (inline SVG in `index.md`) | the running blog page |
| Thread and blog preview pages | `src/thread-page/build.py`, `src/blog-preview/build.py` | `template.html`, `build.py` | `thread.md`, the rendered blog page |

## Setup (macOS)

- Google Chrome, ffmpeg with libx264, Node, Python 3, and FriBiDi: `brew install ffmpeg node fribidi`.
- `cd src && npm install` (installs `puppeteer-core`; the scripts drive your installed Chrome, or `CHROME=<path>`).
- For the timeline videos: `python3 -m venv src/.venv && src/.venv/bin/pip install -r src/timeline-clips/requirements.txt`,
  then pass `PYTHON=$PWD/src/.venv/bin/python`. `make.sh` points Pillow at Homebrew's FriBiDi so text is laid out
  with raqm (kerning), as in the published videos; `render.py` warns if it isn't.
- For the figures: Hugo extended 0.123.0 (the site's CI version), run as `hugo server` from the repo root.
- The HTML pages load fonts from Google Fonts, so render while online.

## Common tasks

Run commands from `x-thread-realtime-rua/`. Write outputs to a scratch folder first and copy them over the
committed files only once they look right.

**Restyle the main video.** Edit `src/main-video/main-video.html`. Scenes: the opening footage with two captions
("Agents are now good at controlling robots." / "But they are slow.", 0-9 s), "How can we make them faster?", one
cup run with each design added in turn (Scene T), vanilla vs pipelining (Scene C), the three real runs (Scene R),
then the end card. Timings are the `ramp`/`win` calls in `render(t)`. They are in scene time: `HOLD` (0.7 s) pauses
at 8.4 s, so after that point the video's clock runs 0.7 s ahead of them. `DUR` is the video's length. Render the
whole video (about 1.5 min), or stills of the page it built:

```bash
src/main-video/make.sh /tmp/mv /tmp/mv.mp4
node src/main-video/render.js /tmp/mv/main-video-built.html stills /tmp/mv/s 3,20,30
```

The second command re-renders stills from the page the first one built. After editing the HTML, rebuild the
page by re-running `make.sh` (or repeat its inline step) before taking stills.

**Restyle the blog's timeline videos (and so the thread clips).** Colours and layout are constants at the top of
`src/timeline-clips/render.py` (`BG`, `PANEL`, `ROBOT_A`, `THINK`, `TOOL`, `CAM`, `RP`, `LP`, ...). The lanes are
drawn in `draw_lanes`, each frame in `compose`, and the cards in `title_card` and `summary_card`. Preview one
frame, render, then re-cut the thread clips from the new videos:

```bash
cd src/timeline-clips && DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib ../.venv/bin/python render.py cups-02 --still 40 /tmp/s.png
PYTHON=$PWD/../.venv/bin/python ./make.sh /tmp/tl            # all three runs, a few minutes each
cd ../.. && TIMELINE=/tmp/tl src/clips/make.sh /tmp/clips
```

`--still -1` is the title card and `--still -2` the summary card. The thread clips' overlays (speed pill, lane
labels, summary labels) are positioned for the current layout. If you change the layout or fix the wording in
`render.py`, drop the overlays instead of re-measuring them (see `src/README.md`, Clips). Replacing the files in
`content/blogs/realtime-rua/img/` changes the blog post itself, so check the post afterwards.

**Re-time the thread clips.** `src/clips/make.sh` calls `retime.sh` with the source speed, the new speed, and three
times in the source video: where the run view starts (after the title card), where it ends, and where the summary
card starts. Find those by stepping through the source with `ffmpeg -ss <t> -i <video> -frames:v 1 f.png`.
The X limit without Premium is 2:20 per video.

**Re-crop the figures.** Start `hugo server`, then `src/figures/make.sh http://localhost:1313 /tmp/figs`. The index
before each name in `make.sh` is the figure number minus one.

**Change the thread.** Edit `thread.md` (posts sit between `---` lines, then a `Media:` line). Rebuild the preview
with `python3 -I src/thread-page/build.py . /tmp/x-thread.html`. It shows X's weighted length: a URL counts 23, and
anything over 280 needs Premium.

## Checking your output

The committed scripts reproduce the committed media, so compare before and after:

- The thread clips and figures 02/03 rebuild byte for byte with the same ffmpeg and Chrome.
- The main video rebuilds frame for frame from `assets/`.
- The timeline videos match the blog's at 44 dB PSNR or better on every frame; the bytes differ by ffmpeg build.

```bash
ffmpeg -i new.mp4 -i old.mp4 -lavfi psnr -f null -          # average PSNR; "inf" means identical frames
ffmpeg -ss 30 -i new.mp4 -frames:v 1 a.png                  # then look at the frame
```

Before committing new media, look at frames from the start, middle and end, including the title and summary cards.

## Conventions

- Call the mechanism **pipelining**, never "the queue", in prose, labels and video text. Real code and the
  messages the model got stay as they are (`kernel.queue`, `queue.jsonl`, `[queue] started`). The blog's timeline
  videos still say "queue" (title pill, status line, lane labels, summary card); fixing that in `render.py` is an
  open task.
- Keep the numbers the same as the blog's table: cups 204 s, 14 actions, robot moving 84%; partly folded towel
  143 s, 11 actions, 67%; crumpled towel 484 s, 32 actions, 78%. All runs: GPT-6 Astra in Codex, effort medium,
  ultrafast tier. Speeds: blog videos 2.5x, 2.5x and 3x; thread clips 3.5x and 8x; main video runs 27x, 17x, 60x.
- The main video's opening is Anthropic's footage and must keep its on-screen credit (`#credit` in
  `main-video.html`).
- Site edits stay inside `content/blogs/realtime-rua/` and this folder. Don't change layouts, the theme or other
  posts.
- GitHub rejects files over 100 MB and warns over 50 MB. Keep new media small.
- Don't post to X; the lab posts.

## Assets

See `src/README.md` (Assets) for every file. In short:

| Folder | What | From |
|---|---|---|
| `assets/opening/` | first 6.2 s of Anthropic's Fable 5.2 video, no audio | YouTube `54Oajk23wbI` |
| `assets/runs/` | front camera videos, `data/` (stages and lanes), `traces/` (Codex rollouts, agent views, timeline, queue journal) | robot-api `docs/demos/`, branch `shao/dsk-real` |
| `assets/cameras/<run>/` | raw front and wrist recordings, `frames.csv` (wall time per frame) | cell PC `~/robot-api-real/agent-runs/<run>/cameras/` |
| `assets/timeline-clips/` | lanes with the code-reading phase cut, `cuts.json` | `trim_lanes.py` |
| `assets/fonts/` | Noto Sans, SIL Open Font License | the cell PC's system fonts |

## Not here

- The full run folders (Codex logs, queue journal, depth frames; 0.6 to 1.8 GB each) stay on the cell PC.
  `lanes.py`, `export_trace.py` and `demo.py` need them and still have the cell PC's paths. Ask Shaoxiong for
  access if you need to recompute the lanes.
- The untrimmed timeline videos from robot-api's `docs/demos/` (the blog uses the trimmed ones).
- `demo.py` may not be the exact version behind robot-api's `pipelining-demo.mp4`.
