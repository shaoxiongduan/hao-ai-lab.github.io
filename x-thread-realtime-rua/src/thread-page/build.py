"""Build the X thread preview page from thread.md.
Usage: python3 -I build.py <launch folder> <out.html>
Media files are referenced as media/<name>; publish them alongside the page."""
import html, json, os, re, subprocess, sys

src, out = sys.argv[1], sys.argv[2]
t = open(os.path.join(src, "thread.md"), encoding="utf-8").read()

# before-posting notes
notes = re.findall(r"^- (.+)$", t.split("\n---\n", 1)[0], re.M)

posts = []
for m in re.finditer(r"\n---\n(\((\d+)/(\d+)\)\s*)(.*?)\n---\nMedia: ([^\n]*)", t, re.S):
    body = m.group(4).strip()
    media = re.findall(r"`([^`]+)`", m.group(5))
    posts.append({"n": int(m.group(2)), "of": int(m.group(3)), "label": m.group(1).strip(), "body": body, "media": media})
assert posts, "no posts parsed"

def weight(s):
    """X's weighted length: URLs count 23; code points outside the light ranges count 2."""
    s2 = re.sub(r"https?://\S+", "", s)
    n = 23 * len(re.findall(r"https?://\S+", s))
    for ch in s2:
        c = ord(ch)
        n += 1 if (c <= 4351 or 8192 <= c <= 8205 or 8208 <= c <= 8223 or 8242 <= c <= 8247) else 2
    return n

def probe(path):
    if path.endswith(".mp4"):
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode())
        return {"kind": "video", "dur": d}
    w, h = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0", path]).decode().strip().split(",")
    return {"kind": "image", "w": int(w), "h": int(h)}

def fmt_dur(d):
    s = int(round(d)); return f"{s // 60}:{s % 60:02d}"

def fmt_mb(b):
    return f"{b / 1e6:.1f} MB" if b >= 1e6 else f"{b / 1e3:.0f} KB"

def rich(text):
    e = html.escape(text, quote=False)
    e = re.sub(r"(https?://[^\s<]+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', e)
    e = re.sub(r"(?<![\w/])@(\w+)", r'<span class="at">@\1</span>', e)
    return e

def note(text):
    e = html.escape(text, quote=False)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e)

cards, total_media = [], {"video": 0, "image": 0}
for p in posts:
    full = p["label"] + " " + p["body"]
    n = weight(full)
    tag = '<span class="len ok">fits in 280</span>' if n <= 280 else '<span class="len long">long post, needs Premium</span>'
    media_html = []
    for name in p["media"]:
        path = os.path.join(src, name)
        info = probe(path); total_media[info["kind"]] += 1
        size = fmt_mb(os.path.getsize(path))
        if info["kind"] == "video":
            el = f'<video src="media/{html.escape(name)}#t=0.1" controls muted playsinline preload="metadata"></video>'
            meta = f'{html.escape(name)} · {fmt_dur(info["dur"])} · {size}'
        else:
            el = f'<img src="media/{html.escape(name)}" alt="Figure attached to post {p["n"]}" width="{info["w"]}" height="{info["h"]}">'
            meta = f'{html.escape(name)} · {info["w"]}×{info["h"]} · {size}'
        media_html.append(f'<figure class="media">{el}<figcaption>{meta}</figcaption></figure>')
    if not media_html:
        media_html.append('<p class="nomedia">No media</p>')
    cards.append(f'''
<article class="post" id="post-{p["n"]}">
  <div class="rail"><span class="num">{p["n"]}</span></div>
  <div class="card">
    <header class="ph">
      <span class="who"><b>Hao AI Lab</b> <span class="handle">@haoailab</span></span>
      <span class="count"><span class="tn">{n}</span> chars {tag}</span>
    </header>
    <p class="text" id="text-{p["n"]}">{rich(full)}</p>
    {"".join(media_html)}
    <footer class="pf">
      <button type="button" class="copy" id="copy-{p["n"]}" data-for="text-{p["n"]}">Copy text</button>
    </footer>
  </div>
</article>''')

longest = max(weight(p["label"] + " " + p["body"]) for p in posts)
page = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html"), encoding="utf-8").read()
page = (page.replace("__POSTS__", "".join(cards))
            .replace("__NOTES__", "".join(f"<li>{note(x)}</li>" for x in notes))
            .replace("__NPOSTS__", str(len(posts)))
            .replace("__NVID__", str(total_media["video"]))
            .replace("__NIMG__", str(total_media["image"]))
            .replace("__LONGEST__", str(longest)))
open(out, "w", encoding="utf-8").write(page)
print(len(posts), "posts;", total_media, "; longest", longest, "; media:", sorted({m for p in posts for m in p["media"]}))
