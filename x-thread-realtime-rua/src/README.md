# Sources for the realtime-rua launch media

These scripts build the X thread's media and the two preview pages. Their inputs are in `../assets/` and in
the blog post's own folder, so nothing else needs downloading. Run them on a Mac with Google Chrome, ffmpeg,
Python 3 and Node. First run `npm install` in this folder (it only installs `puppeteer-core`). If Chrome is
not in `/Applications`, set `CHROME` to its binary. The pages load their fonts from Google Fonts, so stay
online while rendering. The timeline videos need a Python environment of their own:
`python3 -m venv .venv && .venv/bin/pip install -r timeline-clips/requirements.txt`, then `PYTHON=.venv/bin/python`.
They also need FriBiDi (`brew install fribidi`) so Pillow lays text out with raqm (kerning) like the published
videos; `render.py` warns when it can't.

| What | Script | Output |
|---|---|---|
| Main video | `main-video/make.sh <work dir> <out.mp4>` | `01-main-video.mp4` |
| Figures | `figures/make.sh http://localhost:1313 <out dir>` | `02-…`, `03-…`, `04-….png` |
| Timeline videos | `timeline-clips/make.sh <out dir> [run ...]` | the blog's three `<run>-timeline-<speed>x.mp4` |
| Clips | `clips/make.sh <out dir>` | `05-cup-game-3.5x.mp4`, `06-crumpled-towel-8x.mp4` |
| Thread preview page | `python3 -I thread-page/build.py .. <out.html>` | a page showing every post with its media |
| Blog preview page | `python3 -I blog-preview/build.py <rendered post.html> <out.html>` | the post as one standalone page |

## Assets

- `assets/opening/fable52-opening.mp4`: the first 6.2 s of Anthropic's "Claude Fable 5.2 controls physical
  robot arms" video (YouTube `54Oajk23wbI`, 1080p, no audio), cut without re-encoding. The main video uses
  5.9 s of it and credits it on screen.
- `assets/runs/`: a copy of robot-api's `docs/demos/` (branch `shao/dsk-real`) for the three real-cell runs
  (cups-02, towel-fold-18, towel-fold-23). `runs/README.md` describes it:
  - `<run>-front.mp4`: the front camera at real speed (6 fps, 640x480);
  - `data/stages.json` and `data/<run>-lanes.json`: the intervals behind every timeline (schema in
    `data/README.md`);
  - `traces/<run>/`: the Codex rollouts, the agent's views, `timeline.jsonl` and the queue journal (see
    `traces/README.md`);
  - `pipeline.html` and `pipelining-demo.mp4`: robot-api's earlier explainer page and video.
  The untrimmed timeline videos from `docs/demos/` are left out. The blog's trimmed versions in
  `content/blogs/realtime-rua/img/` are the ones the clips use.
- `assets/cameras/<run>/`: the raw front and wrist camera recordings of each run (6 fps, 640x480) and
  `frames.csv`, the wall time of every frame, copied from the cell PC's `~/robot-api-real/agent-runs/<run>/cameras/`.
  The timeline videos are drawn from these.
- `assets/timeline-clips/`: the lanes the timeline videos use, with the code-reading phase at the start of each
  run cut (`trim_lanes.py` writes them from `runs/data/` and `cuts.json`).
- `assets/fonts/`: the Noto Sans fonts the timeline videos use (SIL Open Font License, `LICENSE-noto.txt`).

## Main video

`main-video.html` draws each frame for a time `t` (`window.render(t)`). `render.js` steps it at 30 fps in
headless Chrome and pipes the frames to ffmpeg. `make.sh` does every step:

1. It takes the opening footage as frames.
2. It extracts the front camera of the three runs, sped up to match the lanes (27x, 17x and 60x).
3. `prep.py` turns `stages.json` and `<run>-lanes.json` into `data.json`. The committed `data.json` is its
   output.
4. It inlines `data.json` into the page and renders it.

Built from `assets/`, the output matches `01-main-video.mp4` frame for frame.

The video's whole look (layout, colours, fonts, text, scene timing) is in `main-video.html`; the scene times
are in its `render(t)` function. To try a change, render a few stills instead of the whole video:
`node render.js <work>/main-video-built.html stills <out prefix> 3,20,30` (an absolute path to the page;
times in seconds).

## Figures

Start `hugo server` from the repo root, then run `figures/make.sh`. `figcrop.js` screenshots a figure's
drawing and legend, without its caption, at 2x in light mode. The number before each name in `make.sh` is
the figure's index on the page (Figure N is index N-1).

## Timeline videos

The blog's three demo videos are drawn frame by frame with Pillow by `timeline-clips/render.py`, from the run's
lanes and its three cameras (synced by wall time through `frames.csv`), and piped to ffmpeg. Everything about
their look is in `render.py`: colours and layout at the top (`BG`, `ROBOT_A`, `CAM`, `LP`, ...), the lanes in
`draw_lanes`, the live panel in `compose`, and the title and summary cards in `title_card` and `summary_card`.
They still say "queue" (lane labels, status line, cards); the thread's clips paste over that text.

- `make.sh <out dir>` renders all three; `make.sh <out dir> cups-02` renders one.
- `python render.py cups-02 --still 40 still.png` draws one frame at run time 40 s (-1: title card, -2: summary
  card), which is the quick way to try a change.
- `trim_lanes.py` cuts the code-reading phase from `runs/data/<run>-lanes.json` into `assets/timeline-clips/`.

Rendered on a Mac from `assets/` (with raqm), cups-02 matches the blog's video up to the encoder: every frame
is at 44 dB PSNR or better against it, and the bytes differ only because the cell PC's ffmpeg build was older.

These came from the cell PC too, for reference. They read whole run folders (Codex logs, the queue journal),
which stay on the cell PC, and still have its paths:

- `lanes.py`: computes `<run>-lanes.json` from a run folder.
- `export_trace.py`: exports a run's traces in the published format (`runs/traces/`).
- `demo.py`: robot-api's pipelining demo video, built on `render.py` (`python demo.py STAGES_JSON OUT.mp4`,
  with `DATA` set to `assets/runs/data`). This copy may not be the exact version behind `pipelining-demo.mp4`.

## Clips

`clips/make.sh` uses the blog's own timeline videos in `content/blogs/realtime-rua/img/` (or the folder in
`TIMELINE`, to cut the clips from re-rendered ones):

- `retime.sh` speeds up the run view (2.5x to 3.5x for the cups, 3x to 8x for the towel), keeps 4 s of the
  summary card at normal speed, joins the two with a 0.3 s fade, and drops the title card.
- `overlay.html` (rendered to transparent PNGs by `ovshot.js`) replaces the text baked into the source
  videos: the new speed, "actions" and "WAITING" lane labels instead of "queue", and the summary labels.
  Its positions were measured on the 1280x720 source frames.

To restyle the clips, change `timeline-clips/render.py`, render the timeline videos, and cut the clips from
them with `TIMELINE=<that folder> clips/make.sh <out dir>`. The overlay's positions match the current layout,
so if the layout or the text changes, change the text in `render.py` and drop the overlays (pass a fully
transparent PNG, or remove the `overlay` steps in `retime.sh`).

## Preview pages

`thread-page/build.py` reads `thread.md` and fills `template.html`. It counts each post's length the way X
does (a URL counts 23) and links the media as `media/<name>`, so publish the media files next to the page.

`blog-preview/build.py` takes the post as `hugo server` renders it
(`curl -s http://localhost:1313/blogs/realtime-rua/ -o rendered.html`). It keeps the post body and the
figures' colours, and adds its own title, byline and light/dark styles. The byline comes from the post's
`author` field.
