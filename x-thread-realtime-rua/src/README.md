# Sources for the realtime-rua launch media

These scripts build the X thread's media and the two preview pages. Their inputs are in `../assets/` and in
the blog post's own folder, so nothing else needs downloading. Run them on a Mac with Google Chrome, ffmpeg,
Python 3 and Node. First run `npm install` in this folder (it only installs `puppeteer-core`). If Chrome is
not in `/Applications`, set `CHROME` to its binary. The pages load their fonts from Google Fonts, so stay
online while rendering.

| What | Script | Output |
|---|---|---|
| Main video | `main-video/make.sh <work dir> <out.mp4>` | `01-main-video.mp4` |
| Figures | `figures/make.sh http://localhost:1313 <out dir>` | `02-…`, `03-…`, `04-….png` |
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

## Clips

`clips/make.sh` uses the blog's own timeline videos in `content/blogs/realtime-rua/img/`:

- `retime.sh` speeds up the run view (2.5x to 3.5x for the cups, 3x to 8x for the towel), keeps 4 s of the
  summary card at normal speed, joins the two with a 0.3 s fade, and drops the title card.
- `overlay.html` (rendered to transparent PNGs by `ovshot.js`) replaces the text baked into the source
  videos: the new speed, "actions" and "WAITING" lane labels instead of "queue", and the summary labels.
  Its positions were measured on the 1280x720 source frames.

These scripts only re-time the clips and patch their text. The clips' look (camera panels, lanes, colours,
fonts, title and summary cards) is baked into the blog's timeline videos. The script that rendered those
videos is not in this repo or in any robot-api branch: it is only on the cell PC. It also used the wrist
cameras, whose recordings are only in the run folders on the cell PC (`~/robot-api-real/agent-runs/<run>/`).
To restyle the clips, either bring that script over or draw the clips like the main video's real-run scene
(lanes from `data/<run>-lanes.json`, video from `<run>-front.mp4`).

## Preview pages

`thread-page/build.py` reads `thread.md` and fills `template.html`. It counts each post's length the way X
does (a URL counts 23) and links the media as `media/<name>`, so publish the media files next to the page.

`blog-preview/build.py` takes the post as `hugo server` renders it
(`curl -s http://localhost:1313/blogs/realtime-rua/ -o rendered.html`). It keeps the post body and the
figures' colours, and adds its own title, byline and light/dark styles. The byline comes from the post's
`author` field.
