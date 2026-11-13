# Sources for the realtime-rua launch media

These scripts build the X thread's media and the two preview pages. Run them on a Mac with Google Chrome,
ffmpeg, Python 3 and Node. First run `npm install` in this folder (it only installs `puppeteer-core`). If
Chrome is not in `/Applications`, set `CHROME` to its binary.

| What | Script | Output |
|---|---|---|
| Main video | `main-video/make.sh <opening footage> <run data> <work dir> <out.mp4>` | `01-main-video.mp4` |
| Figures | `figures/make.sh http://localhost:1313 <out dir>` | `02-…`, `03-…`, `04-….png` |
| Clips | `clips/make.sh <out dir>` | `05-cup-game-3.5x.mp4`, `06-crumpled-towel-8x.mp4` |
| Thread preview page | `python3 -I thread-page/build.py .. <out.html>` | a page showing every post with its media |
| Blog preview page | `python3 -I blog-preview/build.py <rendered post.html> <out.html>` | the post as one standalone page |

## Main video

`main-video.html` draws each frame for a time `t` (`window.render(t)`). `render.js` steps it at 30 fps in
headless Chrome and pipes the frames to ffmpeg. `make.sh` does every step:

1. It takes the first 5.9 s of Anthropic's "Claude Fable 5.2 controls physical robot arms" video
   (YouTube `54Oajk23wbI`, 1080p) as frames for the opening. The footage is not in this repo, and the video
   credits it on screen.
2. It extracts the front camera of the three runs, sped up to match the lanes (27x, 17x and 60x).
3. `prep.py` turns `stages.json` and `<run>-lanes.json` into `data.json`. The committed `data.json` is its
   output.
4. It inlines `data.json` into the page and renders it.

The run data (`stages.json`, `<run>-lanes.json`, `<run>-front.mp4` for cups-02, towel-fold-18 and
towel-fold-23) is robot-api's demo data and is not in this repo.

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

## Preview pages

`thread-page/build.py` reads `thread.md` and fills `template.html`. It counts each post's length the way X
does (a URL counts 23) and links the media as `media/<name>`, so publish the media files next to the page.

`blog-preview/build.py` takes the post as `hugo server` renders it
(`curl -s http://localhost:1313/blogs/realtime-rua/ -o rendered.html`). It keeps the post body and the
figures' colours, and adds its own title, byline and light/dark styles. The byline comes from the post's
`author` field.
