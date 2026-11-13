"""Build the artifact page from Hugo's rendered realtime-rua post.

Usage: python3 -I build.py <rendered.html> <out.html>
Takes the post body (everything inside .post-content), rewrites its theme variables to the artifact's
light/dark token pattern, and wraps it in a standalone article shell.
"""
import re
import sys

src, out = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()

start_tag = '<div class="post-content post-content-justified">'
i = html.index(start_tag) + len(start_tag)
j = re.compile(r'<footer class="?post-footer"?>').search(html, i).start()   # quotes vary with --minify
body = html[i:j]
body = body[: body.rindex("</div>")]          # drop the .post-content closing tag

# The post's theme: :root{--r-*} for light and body.dark{--r-*} for dark -> artifact token pattern.
m = re.search(r"body\.dark\{([^}]*)\}", body)
dark = m.group(1)
body = body.replace(m.group(0), "")
body = body.replace("var(--secondary)", "var(--muted)")

authors = re.search(r'<meta name="?author"? content="([^"]+)"', html).group(1)
title = re.search(r'<h1 class="?post-title[^>]*>\s*(.*?)\s*</h1>', html, re.S).group(1).strip()
words = len(re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<[^>]+>", " ", body, flags=re.S).split())
minutes = max(1, round(words / 230))

shell = f"""<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="Robot-use agents score well on benchmarks whose simulators wait for the model, but on a real robot every second of thinking is a second the robot stands still.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: one reading column, figures at column width; the post's own figure palette (think / tool / robot) carries the colour. */
:root{{
  --bg:#fbfbfd; --surface:#ffffff; --fg:#16181d; --muted:#5b6170; --rule:#e3e5eb; --accent:#3c56c9; --code-bg:#f2f3f7;
  --display:"Archivo","Helvetica Neue",Arial,sans-serif;
  --body:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;
  --figfont:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen,Ubuntu,Cantarell,"Open Sans","Helvetica Neue",sans-serif;
}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{
  --bg:#1d1e20; --surface:#232427; --fg:#e7e9ee; --muted:#a3a9b5; --rule:#33363d; --accent:#8ea3ff; --code-bg:#2a2c31; color-scheme:dark;
  {dark}
}}}}
:root[data-theme="dark"]{{
  --bg:#1d1e20; --surface:#232427; --fg:#e7e9ee; --muted:#a3a9b5; --rule:#33363d; --accent:#8ea3ff; --code-bg:#2a2c31; color-scheme:dark;
  {dark}
}}
body{{background:var(--bg);color:var(--fg);font-family:var(--body);font-size:17.5px;line-height:1.65;-webkit-font-smoothing:antialiased}}
.page{{max-width:860px;margin:0 auto;padding-left:max(16px, env(safe-area-inset-left, 0px));padding-right:max(16px, env(safe-area-inset-right, 0px));padding-block:40px 64px}}
.masthead{{display:grid;gap:14px;padding-bottom:28px;border-bottom:1px solid var(--rule);margin-bottom:32px}}
.eyebrow{{font-family:var(--display);font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
.eyebrow b{{color:var(--fg)}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(30px,5vw,44px);line-height:1.1;letter-spacing:-.01em;margin:0;text-wrap:balance}}
.byline{{font-family:var(--display);font-size:15px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 14px}}
.byline .authors{{color:var(--fg);font-weight:500}}
a{{color:var(--accent);text-underline-offset:2px}}
a:focus-visible{{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px}}
.post-content{{min-width:0}}
.post-content > p,.post-content li{{hyphens:auto}}
.post-content p{{margin:0 0 1.1em}}
.post-content ul,.post-content ol{{padding-left:1.3em;margin:0 0 1.2em}}
.post-content li{{margin:.35em 0}}
.post-content h2{{font-family:var(--display);font-weight:700;font-size:26px;line-height:1.25;margin:2.2em 0 .7em;text-wrap:balance}}
.post-content h3{{font-family:var(--display);font-weight:600;font-size:20px;margin:1.8em 0 .6em}}
.post-content strong,.post-content b{{font-weight:600}}
.post-content code{{font-family:var(--mono);font-size:.84em;background:var(--code-bg);padding:.1em .35em;border-radius:4px}}
.post-content pre{{font-family:var(--mono);font-size:14px;line-height:1.55;background:var(--code-bg);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;overflow-x:auto;margin:0 0 1.3em}}
.post-content pre code{{background:none;padding:0;font-size:inherit}}
.post-content .highlight pre{{border:none}}
.post-content figure{{margin:28px 0 30px}}
.post-content figcaption{{font-family:var(--display)}}
body .post-content .rua-fig svg text{{font-family:var(--figfont)}}
body .post-content .rua-legend{{font-family:var(--figfont)}}
.post-content table{{border-collapse:collapse;width:100%;font-family:var(--display);font-size:15px}}
.post-content th,.post-content td{{border-bottom:1px solid var(--rule);padding:9px 10px;vertical-align:top;text-align:left}}
.post-content th{{font-weight:600;color:var(--muted);font-size:13.5px}}
.post-content .rua-tbl p{{font-size:14px;color:var(--muted)}}
.post-content .rua-ref{{font-family:var(--display);font-size:14.5px;line-height:1.5}}
.post-content .anchor{{display:none}}
.post-content img,.post-content video{{max-width:100%}}
.foot{{margin-top:48px;padding-top:20px;border-top:1px solid var(--rule);font-family:var(--display);font-size:14px;color:var(--muted)}}
@media (max-width:560px){{body{{font-size:16.5px}} .page{{padding-block:24px 48px}} .post-content h2{{font-size:22px}}}}
@media (prefers-reduced-motion: reduce){{*{{scroll-behavior:auto}}}}
</style>
<main class="page">
  <header class="masthead">
    <div class="eyebrow"><b>Hao AI Lab</b> &middot; Blog preview</div>
    <h1>{title}</h1>
    <div class="byline"><span class="authors">{authors}</span><span>November 11, 2026</span><span>{minutes} min read</span></div>
  </header>
  <article class="post-content">
{body}
  </article>
  <footer class="foot">Preview of a Hao AI Lab blog post. Follow <a href="https://x.com/haoailab">@haoailab</a> for updates.</footer>
</main>
"""
open(out, "w", encoding="utf-8").write(shell)
print(f"{title} | {words} words, {minutes} min | {len(shell)} bytes")
